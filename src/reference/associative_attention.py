"""A tiny attention head for contextual key-value recall.

The mapping from keys to values changes in every example. The model therefore
cannot store the answers in its parameters; it must select the matching record
from the supplied context and copy that record's value.
"""

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

IntArray = NDArray[np.int64]
FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class RecallBatch:
    memory_keys: IntArray
    memory_values: IntArray
    queries: IntArray
    targets: IntArray
    target_slots: IntArray

    def __len__(self) -> int:
        return len(self.queries)


def generate_recall_batch(
    random: np.random.Generator,
    examples: int,
    key_count: int = 16,
    value_count: int = 8,
    memory_size: int = 8,
) -> RecallBatch:
    """Generate novel key-value bindings and one query per context."""
    if not 1 <= memory_size <= min(key_count, value_count):
        raise ValueError("memory_size must fit both token vocabularies")

    memory_keys = np.empty((examples, memory_size), dtype=np.int64)
    memory_values = np.empty((examples, memory_size), dtype=np.int64)
    target_slots = random.integers(memory_size, size=examples, dtype=np.int64)

    for row in range(examples):
        memory_keys[row] = random.choice(key_count, memory_size, replace=False)
        memory_values[row] = random.choice(value_count, memory_size, replace=False)

    rows = np.arange(examples)
    queries = memory_keys[rows, target_slots]
    targets = memory_values[rows, target_slots]
    return RecallBatch(memory_keys, memory_values, queries, targets, target_slots)


class AssociativeAttention:
    """One learned query/key head followed by parameter-free value copying."""

    def __init__(self, key_count: int, width: int, seed: int = 6809) -> None:
        random = np.random.default_rng(seed)
        scale = 1.0 / math.sqrt(width)
        self.query_embeddings = random.normal(0.0, scale, (key_count, width))
        self.key_embeddings = random.normal(0.0, scale, (key_count, width))
        self.width = width

    @property
    def parameters(self) -> int:
        return self.query_embeddings.size + self.key_embeddings.size

    def scores(self, batch: RecallBatch) -> FloatArray:
        queries = self.query_embeddings[batch.queries]
        keys = self.key_embeddings[batch.memory_keys]
        return np.einsum("bd,bmd->bm", queries, keys) / math.sqrt(self.width)

    def attention(self, batch: RecallBatch) -> FloatArray:
        scores = self.scores(batch)
        scores -= scores.max(axis=1, keepdims=True)
        weights = np.exp(scores)
        return weights / weights.sum(axis=1, keepdims=True)

    def predict(self, batch: RecallBatch) -> IntArray:
        slots = self.scores(batch).argmax(axis=1)
        return batch.memory_values[np.arange(len(batch)), slots]

    def accuracy(self, batch: RecallBatch) -> float:
        return float(np.mean(self.predict(batch) == batch.targets))

    def slot_cross_entropy_bits(self, batch: RecallBatch) -> float:
        weights = self.attention(batch)
        probability = weights[np.arange(len(batch)), batch.target_slots]
        return float(np.mean(-np.log2(probability)))

    def train(
        self,
        batch: RecallBatch,
        epochs: int = 80,
        learning_rate: float = 0.5,
    ) -> list[float]:
        """Train key matching; the changing key-value mapping is never learned."""
        losses: list[float] = []
        rows = np.arange(len(batch))
        root_width = math.sqrt(self.width)

        for _ in range(epochs):
            query_vectors = self.query_embeddings[batch.queries]
            key_vectors = self.key_embeddings[batch.memory_keys]
            weights = self.attention(batch)
            losses.append(self.slot_cross_entropy_bits(batch))

            score_gradient = weights
            score_gradient[rows, batch.target_slots] -= 1.0
            score_gradient /= len(batch)

            query_gradient = (
                np.einsum("bm,bmd->bd", score_gradient, key_vectors) / root_width
            )
            key_gradient = (
                score_gradient[:, :, np.newaxis]
                * query_vectors[:, np.newaxis, :]
                / root_width
            )

            query_updates = np.zeros_like(self.query_embeddings)
            key_updates = np.zeros_like(self.key_embeddings)
            np.add.at(query_updates, batch.queries, query_gradient)
            np.add.at(key_updates, batch.memory_keys, key_gradient)
            self.query_embeddings -= learning_rate * query_updates
            self.key_embeddings -= learning_rate * key_updates

        return losses

    def quantized_copy(self, fractional_bits: int = 4) -> "AssociativeAttention":
        destination = AssociativeAttention(
            len(self.query_embeddings), self.width, seed=0
        )
        scale = 1 << fractional_bits
        destination.query_embeddings = (
            np.clip(np.rint(self.query_embeddings * scale), -128, 127).astype(
                np.float64
            )
            / scale
        )
        destination.key_embeddings = (
            np.clip(np.rint(self.key_embeddings * scale), -128, 127).astype(np.float64)
            / scale
        )
        return destination


def global_lookup_predictions(
    training: RecallBatch, evaluation: RecallBatch, value_count: int
) -> IntArray:
    """Best parameter-only key-to-value lookup learned from training examples."""
    key_count = max(training.memory_keys.max(), evaluation.memory_keys.max()) + 1
    counts = np.zeros((key_count, value_count), dtype=np.int64)
    np.add.at(counts, (training.queries, training.targets), 1)
    return counts.argmax(axis=1)[evaluation.queries]


def tail_oracle_predictions(
    training: RecallBatch,
    evaluation: RecallBatch,
    value_count: int,
    visible_records: int,
) -> IntArray:
    """An optimistic fixed-window baseline that recalls any visible binding."""
    predictions = global_lookup_predictions(training, evaluation, value_count)
    start = evaluation.memory_keys.shape[1] - visible_records
    for row, query in enumerate(evaluation.queries):
        matches = np.flatnonzero(evaluation.memory_keys[row, start:] == query)
        if len(matches):
            predictions[row] = evaluation.memory_values[row, start + matches[0]]
    return predictions
