"""Reference models and measurements for EXP-006 tab completion."""

from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray
from token_lm import BOUNDARY

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]
ByteArray = NDArray[np.int8]


def load_phrases(path: Path) -> list[str]:
    return [
        line.strip().upper()
        for line in path.read_text(encoding="ascii").splitlines()
        if line.strip()
    ]


def build_completion_vocabulary(
    phrases: Sequence[str],
) -> tuple[list[str], dict[str, int]]:
    vocabulary = [BOUNDARY] + sorted(
        {word for phrase in phrases for word in phrase.split()}
    )
    return vocabulary, {word: index for index, word in enumerate(vocabulary)}


def make_completion_examples(
    phrases: Sequence[str],
    token_by_text: dict[str, int],
    context_size: int,
) -> tuple[IntArray, IntArray]:
    contexts: list[list[int]] = []
    targets: list[int] = []
    boundary = token_by_text[BOUNDARY]

    for phrase in phrases:
        context = [boundary] * context_size
        sequence = [token_by_text[word] for word in phrase.split()] + [boundary]
        for target in sequence:
            contexts.append(context.copy())
            targets.append(target)
            context = context[1:] + [target]

    return np.asarray(contexts, dtype=np.int64), np.asarray(targets, dtype=np.int64)


class Predictor(Protocol):
    vocabulary: list[str]
    token_by_text: dict[str, int]

    def scores(self, context: IntArray) -> FloatArray: ...


@dataclass(frozen=True)
class CompletionMetrics:
    examples: int
    lexical_examples: int
    cross_entropy: float
    top_one_accuracy: float
    top_three_accuracy: float
    typed_characters: int
    completion_keystrokes: int
    keystroke_savings: float


@dataclass(frozen=True)
class NeuralConfig:
    context: int = 4
    embedding: int = 8
    hidden: int = 0
    seed: int = 6809


class Adam:
    def __init__(
        self,
        parameters: Sequence[FloatArray],
        *,
        learning_rate: float,
        beta_one: float = 0.9,
        beta_two: float = 0.999,
        epsilon: float = 1e-8,
    ):
        self.parameters = list(parameters)
        self.learning_rate = learning_rate
        self.beta_one = beta_one
        self.beta_two = beta_two
        self.epsilon = epsilon
        self.first = [np.zeros_like(parameter) for parameter in parameters]
        self.second = [np.zeros_like(parameter) for parameter in parameters]
        self.step = 0

    def update(self, gradients: Sequence[FloatArray]) -> None:
        self.step += 1
        first_scale = 1.0 - self.beta_one**self.step
        second_scale = 1.0 - self.beta_two**self.step
        for index, (parameter, gradient) in enumerate(
            zip(self.parameters, gradients, strict=True)
        ):
            self.first[index] *= self.beta_one
            self.first[index] += (1.0 - self.beta_one) * gradient
            self.second[index] *= self.beta_two
            self.second[index] += (1.0 - self.beta_two) * gradient * gradient
            corrected_first = self.first[index] / first_scale
            corrected_second = self.second[index] / second_scale
            parameter -= (
                self.learning_rate
                * corrected_first
                / (np.sqrt(corrected_second) + self.epsilon)
            )


class AdditiveCompletionModel:
    """Positional embeddings followed directly by an output projection."""

    def __init__(self, config: NeuralConfig, vocabulary: Sequence[str]):
        if config.hidden:
            raise ValueError("additive model does not use a hidden layer")
        self.config = config
        self.vocabulary = list(vocabulary)
        self.token_by_text = {
            token: index for index, token in enumerate(self.vocabulary)
        }
        self.vocabulary_size = len(self.vocabulary)
        random = np.random.Generator(np.random.PCG64(config.seed))
        scale = math.sqrt(2.0 / (self.vocabulary_size + config.embedding))
        self.position_embeddings = random.normal(
            0.0,
            scale,
            (config.context, self.vocabulary_size, config.embedding),
        )
        self.output_weights = random.normal(
            0.0,
            scale,
            (self.vocabulary_size, config.embedding),
        )
        self.output_biases = np.zeros(self.vocabulary_size, dtype=np.float64)

    @property
    def parameters(self) -> tuple[FloatArray, ...]:
        return (
            self.position_embeddings,
            self.output_weights,
            self.output_biases,
        )

    @property
    def parameter_count(self) -> int:
        return sum(parameter.size for parameter in self.parameters)

    def _batch_forward(self, contexts: IntArray) -> tuple[FloatArray, FloatArray]:
        context_vectors = np.zeros(
            (len(contexts), self.config.embedding), dtype=np.float64
        )
        for position in range(self.config.context):
            context_vectors += self.position_embeddings[position, contexts[:, position]]
        logits = context_vectors @ self.output_weights.T + self.output_biases
        return context_vectors, logits

    def scores(self, context: IntArray) -> FloatArray:
        return self._batch_forward(context.reshape(1, -1))[1][0]

    def train_batch(
        self, contexts: IntArray, targets: IntArray, optimizer: Adam
    ) -> float:
        context_vectors, logits = self._batch_forward(contexts)
        probabilities, loss = softmax_loss(logits, targets)
        probabilities[np.arange(len(targets)), targets] -= 1.0
        output_error = probabilities / len(targets)

        output_weight_gradient = output_error.T @ context_vectors
        output_bias_gradient = np.sum(output_error, axis=0)
        context_error = output_error @ self.output_weights
        embedding_gradient = np.zeros_like(self.position_embeddings)
        for position in range(self.config.context):
            np.add.at(
                embedding_gradient[position],
                contexts[:, position],
                context_error,
            )
        optimizer.update(
            (
                embedding_gradient,
                output_weight_gradient,
                output_bias_gradient,
            )
        )
        return loss

    def quantized_copy(self) -> AdditiveCompletionModel:
        clone = AdditiveCompletionModel(self.config, self.vocabulary)
        for destination, source in zip(clone.parameters, self.parameters, strict=True):
            destination[:] = quantize_q4_4(source)
        return clone

    def int8_copy(self) -> Int8AdditiveModel:
        return Int8AdditiveModel(
            self.config,
            self.vocabulary,
            tuple(
                np.rint(quantize_q4_4(parameter) * 16.0).astype(np.int8)
                for parameter in self.parameters
            ),
        )


class Int8AdditiveModel:
    """Bit-exact inference view of the exported Q4.4 additive model."""

    def __init__(
        self,
        config: NeuralConfig,
        vocabulary: Sequence[str],
        parameters: tuple[ByteArray, ByteArray, ByteArray],
    ):
        self.config = config
        self.vocabulary = list(vocabulary)
        self.token_by_text = {
            token: index for index, token in enumerate(self.vocabulary)
        }
        (
            self.position_embeddings,
            self.output_weights,
            self.output_biases,
        ) = parameters

    @property
    def parameters(self) -> tuple[ByteArray, ...]:
        return (
            self.position_embeddings,
            self.output_weights,
            self.output_biases,
        )

    @property
    def parameter_count(self) -> int:
        return sum(parameter.size for parameter in self.parameters)

    @property
    def inference_multiplies(self) -> int:
        return len(self.vocabulary) * self.config.embedding

    def context_vector(self, context: IntArray) -> IntArray:
        vector = np.zeros(self.config.embedding, dtype=np.int64)
        for position, token in enumerate(context):
            vector += self.position_embeddings[position, int(token)].astype(np.int64)
        return vector

    def integer_scores(self, context: IntArray) -> IntArray:
        context_vector = self.context_vector(context)
        return (
            self.output_weights.astype(np.int64) @ context_vector
            + self.output_biases.astype(np.int64) * 16
        )

    def scores(self, context: IntArray) -> FloatArray:
        return self.integer_scores(context).astype(np.float64)

    def model_bytes(self, *, padded_size: int | None = None) -> bytes:
        payload = b"".join(
            parameter.tobytes(order="C") for parameter in self.parameters
        )
        if padded_size is None:
            return payload
        if len(payload) > padded_size:
            raise ValueError(
                f"{len(payload)} model bytes exceed {padded_size}-byte image"
            )
        return payload + bytes(padded_size - len(payload))


class HiddenCompletionModel:
    """Positional embeddings, one ReLU layer, and an output projection."""

    def __init__(self, config: NeuralConfig, vocabulary: Sequence[str]):
        if config.hidden < 1:
            raise ValueError("hidden model requires a hidden layer")
        self.config = config
        self.vocabulary = list(vocabulary)
        self.token_by_text = {
            token: index for index, token in enumerate(self.vocabulary)
        }
        self.vocabulary_size = len(self.vocabulary)
        random = np.random.Generator(np.random.PCG64(config.seed))
        embedding_scale = math.sqrt(2.0 / (self.vocabulary_size + config.embedding))
        hidden_scale = math.sqrt(2.0 / config.embedding)
        output_scale = math.sqrt(2.0 / config.hidden)
        self.position_embeddings = random.normal(
            0.0,
            embedding_scale,
            (config.context, self.vocabulary_size, config.embedding),
        )
        self.hidden_weights = random.normal(
            0.0, hidden_scale, (config.hidden, config.embedding)
        )
        self.hidden_biases = np.full(config.hidden, 0.05, dtype=np.float64)
        self.output_weights = random.normal(
            0.0, output_scale, (self.vocabulary_size, config.hidden)
        )
        self.output_biases = np.zeros(self.vocabulary_size, dtype=np.float64)

    @property
    def parameters(self) -> tuple[FloatArray, ...]:
        return (
            self.position_embeddings,
            self.hidden_weights,
            self.hidden_biases,
            self.output_weights,
            self.output_biases,
        )

    @property
    def parameter_count(self) -> int:
        return sum(parameter.size for parameter in self.parameters)

    @property
    def inference_multiplies(self) -> int:
        return (
            self.config.embedding * self.config.hidden
            + self.config.hidden * self.vocabulary_size
        )

    def _batch_forward(
        self, contexts: IntArray
    ) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
        context_vectors = np.zeros(
            (len(contexts), self.config.embedding), dtype=np.float64
        )
        for position in range(self.config.context):
            context_vectors += self.position_embeddings[position, contexts[:, position]]
        hidden_pre = context_vectors @ self.hidden_weights.T + self.hidden_biases
        hidden = np.maximum(hidden_pre, 0.0)
        logits = hidden @ self.output_weights.T + self.output_biases
        return context_vectors, hidden_pre, hidden, logits

    def scores(self, context: IntArray) -> FloatArray:
        return self._batch_forward(context.reshape(1, -1))[3][0]

    def train_batch(
        self, contexts: IntArray, targets: IntArray, optimizer: Adam
    ) -> float:
        context_vectors, hidden_pre, hidden, logits = self._batch_forward(contexts)
        probabilities, loss = softmax_loss(logits, targets)
        probabilities[np.arange(len(targets)), targets] -= 1.0
        output_error = probabilities / len(targets)

        output_weight_gradient = output_error.T @ hidden
        output_bias_gradient = np.sum(output_error, axis=0)
        hidden_error = output_error @ self.output_weights
        hidden_pre_error = hidden_error * (hidden_pre > 0.0)
        hidden_weight_gradient = hidden_pre_error.T @ context_vectors
        hidden_bias_gradient = np.sum(hidden_pre_error, axis=0)
        context_error = hidden_pre_error @ self.hidden_weights
        embedding_gradient = np.zeros_like(self.position_embeddings)
        for position in range(self.config.context):
            np.add.at(
                embedding_gradient[position],
                contexts[:, position],
                context_error,
            )
        optimizer.update(
            (
                embedding_gradient,
                hidden_weight_gradient,
                hidden_bias_gradient,
                output_weight_gradient,
                output_bias_gradient,
            )
        )
        return loss

    def quantized_copy(self) -> HiddenCompletionModel:
        clone = HiddenCompletionModel(self.config, self.vocabulary)
        for destination, source in zip(clone.parameters, self.parameters, strict=True):
            destination[:] = quantize_q4_4(source)
        return clone


class FrequencyPredictor:
    def __init__(
        self,
        vocabulary: Sequence[str],
        targets: IntArray,
    ):
        self.vocabulary = list(vocabulary)
        self.token_by_text = {
            token: index for index, token in enumerate(self.vocabulary)
        }
        self.counts = np.bincount(targets, minlength=len(self.vocabulary)).astype(
            np.float64
        )

    def scores(self, context: IntArray) -> FloatArray:
        del context
        return np.log(self.counts + 0.25)


class BackoffNGramPredictor:
    def __init__(
        self,
        vocabulary: Sequence[str],
        contexts: IntArray,
        targets: IntArray,
    ):
        self.vocabulary = list(vocabulary)
        self.token_by_text = {
            token: index for index, token in enumerate(self.vocabulary)
        }
        self.context_size = contexts.shape[1]
        self.counts: list[dict[tuple[int, ...], Counter[int]]] = [
            defaultdict(Counter) for _ in range(self.context_size + 1)
        ]
        for context, target in zip(contexts, targets, strict=True):
            for length in range(self.context_size + 1):
                key = tuple(int(value) for value in context[-length:]) if length else ()
                self.counts[length][key][int(target)] += 1

    @property
    def stored_counts(self) -> int:
        return sum(len(counter) for table in self.counts for counter in table.values())

    def scores(self, context: IntArray) -> FloatArray:
        for length in range(self.context_size, -1, -1):
            key = tuple(int(value) for value in context[-length:]) if length else ()
            if key in self.counts[length]:
                counter = self.counts[length][key]
                values = np.full(len(self.vocabulary), 0.25, dtype=np.float64)
                for token, count in counter.items():
                    values[token] += count
                return np.log(values)
        raise AssertionError("unigram context must exist")


def softmax_loss(logits: FloatArray, targets: IntArray) -> tuple[FloatArray, float]:
    shifted = logits - np.max(logits, axis=1, keepdims=True)
    exponentials = np.exp(shifted)
    probabilities = exponentials / np.sum(exponentials, axis=1, keepdims=True)
    selected = probabilities[np.arange(len(targets)), targets]
    loss = -float(np.mean(np.log(np.maximum(selected, 1e-12))))
    return probabilities, loss


def train_neural_model(
    model: AdditiveCompletionModel | HiddenCompletionModel,
    contexts: IntArray,
    targets: IntArray,
    *,
    epochs: int,
    learning_rate: float,
    batch_size: int,
) -> list[float]:
    optimizer = Adam(model.parameters, learning_rate=learning_rate)
    random = np.random.Generator(np.random.PCG64(model.config.seed))
    losses: list[float] = []
    for _ in range(epochs):
        order = random.permutation(len(targets))
        total = 0.0
        for start in range(0, len(order), batch_size):
            indices = order[start : start + batch_size]
            loss = model.train_batch(contexts[indices], targets[indices], optimizer)
            total += loss * len(indices)
        losses.append(total / len(targets))
    return losses


def quantize_q4_4(values: FloatArray) -> FloatArray:
    return np.clip(np.rint(values * 16.0), -128, 127) / 16.0


def evaluate(
    predictor: Predictor,
    contexts: IntArray,
    targets: IntArray,
) -> CompletionMetrics:
    boundary = predictor.token_by_text[BOUNDARY]
    losses: list[float] = []
    top_one = 0
    top_three = 0
    lexical_examples = 0
    typed_characters = 0
    completion_keystrokes = 0

    for context, target_value in zip(contexts, targets, strict=True):
        target = int(target_value)
        scores = predictor.scores(context)
        shifted = scores - np.max(scores)
        probability = math.exp(float(shifted[target])) / float(np.sum(np.exp(shifted)))
        losses.append(-math.log(max(probability, 1e-12)))
        if target == boundary:
            continue

        lexical_examples += 1
        lexical_scores = scores.copy()
        lexical_scores[boundary] = -math.inf
        ranking = np.argsort(-lexical_scores, kind="stable")
        top_one += int(ranking[0] == target)
        top_three += int(target in ranking[:3])

        word = predictor.vocabulary[target]
        typed_characters += len(word)
        cost = len(word)
        for prefix_length in range(len(word)):
            prefix = word[:prefix_length]
            compatible = [
                index
                for index, candidate in enumerate(predictor.vocabulary)
                if index != boundary and candidate.startswith(prefix)
            ]
            if not compatible:
                continue
            suggestion = max(
                compatible,
                key=lambda index: (float(scores[index]), -index),
            )
            candidate_cost = prefix_length + 1
            if suggestion == target and candidate_cost < cost:
                cost = candidate_cost
                break
        completion_keystrokes += cost

    return CompletionMetrics(
        examples=len(targets),
        lexical_examples=lexical_examples,
        cross_entropy=float(np.mean(losses)),
        top_one_accuracy=top_one / lexical_examples,
        top_three_accuracy=top_three / lexical_examples,
        typed_characters=typed_characters,
        completion_keystrokes=completion_keystrokes,
        keystroke_savings=1.0 - completion_keystrokes / typed_characters,
    )


def suggest(
    predictor: Predictor,
    words: Sequence[str],
    *,
    prefix: str = "",
    count: int = 3,
) -> list[str]:
    boundary = predictor.token_by_text[BOUNDARY]
    context = [boundary] * 4
    for word in words[-4:]:
        context = context[1:] + [predictor.token_by_text[word.upper()]]
    scores = predictor.scores(np.asarray(context, dtype=np.int64))
    candidates = [
        index
        for index, word in enumerate(predictor.vocabulary)
        if index != boundary and word.startswith(prefix.upper())
    ]
    candidates.sort(key=lambda index: (-float(scores[index]), index))
    return [predictor.vocabulary[index] for index in candidates[:count]]


def parameter_checksum(parameters: Iterable[FloatArray]) -> str:
    digest = hashlib.sha256()
    for parameter in parameters:
        digest.update(parameter.astype("<f8", copy=False).tobytes())
    return digest.hexdigest()


def largest_additive_embedding(
    vocabulary_size: int, context_size: int, budget: int
) -> int:
    return (budget - vocabulary_size) // (vocabulary_size * (context_size + 1))


def largest_hidden_width(
    vocabulary_size: int,
    context_size: int,
    embedding_size: int,
    budget: int,
) -> int:
    fixed = context_size * vocabulary_size * embedding_size + vocabulary_size
    per_hidden = embedding_size + 1 + vocabulary_size
    return (budget - fixed) // per_hidden
