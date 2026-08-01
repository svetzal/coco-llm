"""Melody model and table baselines for EXP-010.

The model is the same additive shape as every other in this project: each
context position contributes an embedding, the embeddings are summed, and one
linear layer produces logits. No hidden layer, no attention.

Two things differ from EXP-008. Each context position carries only the tokens
that can appear in it — mode positions hold two, chord seven, beat eight,
melody twenty-eight — because a rectangular table would cost roughly half the
available context at this budget. And the model is trained in floating point
here: this phase asks only whether the architecture can beat a table at all,
and if it cannot in float it certainly cannot after quantization.

The baselines are interpolated backoff tables, deliberately strong. Making the
baseline weak is the easiest way to get a result that means nothing.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from melody_tokens import MAX_BEATS, MELODY_TOKENS, METRES, MODES, Tune
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]

# Melody history before the start of a tune. An input-only token.
PAD = MELODY_TOKENS
MELODY_INPUTS = MELODY_TOKENS + 1

MODE_INPUTS = len(MODES)
METRE_INPUTS = len(METRES)
CHORD_INPUTS = 7
BEAT_INPUTS = MAX_BEATS + 4  # 3/2 has twelve rows to the bar

SITUATIONAL = (MODE_INPUTS, METRE_INPUTS, CHORD_INPUTS, BEAT_INPUTS)


@dataclass(frozen=True)
class MelodyConfig:
    history: int = 18
    embedding: int = 6
    seed: int = 6809
    situational: bool = True

    @property
    def position_sizes(self) -> tuple[int, ...]:
        prefix = SITUATIONAL if self.situational else ()
        return (*prefix, *([MELODY_INPUTS] * self.history))

    @property
    def context(self) -> int:
        return len(self.position_sizes)

    @property
    def parameters(self) -> int:
        rows = sum(self.position_sizes)
        return rows * self.embedding + MELODY_TOKENS * self.embedding + MELODY_TOKENS


def build_examples(
    tunes: Sequence[Tune], config: MelodyConfig
) -> tuple[IntArray, IntArray]:
    """One example per row: its context, and the token that follows."""
    contexts: list[list[int]] = []
    targets: list[int] = []

    for tune in tunes:
        mode = MODES.index(tune.mode)
        metre = METRES.index(tune.metre)
        history = [PAD] * config.history

        for row in range(tune.rows):
            prefix = (
                [mode, metre, tune.chords[row], tune.beats[row]]
                if config.situational
                else []
            )
            contexts.append([*prefix, *history])
            targets.append(tune.melody[row])
            history = history[1:] + [tune.melody[row]]

    return (
        np.asarray(contexts, dtype=np.int64),
        np.asarray(targets, dtype=np.int64),
    )


class MelodyModel:
    def __init__(self, config: MelodyConfig):
        self.config = config
        random = np.random.Generator(np.random.PCG64(config.seed))
        self.embeddings = [
            random.normal(0.0, 0.08, (size, config.embedding))
            for size in config.position_sizes
        ]
        self.weights = random.normal(0.0, 0.08, (MELODY_TOKENS, config.embedding))
        self.biases = np.zeros(MELODY_TOKENS, dtype=np.float64)

    def context_vectors(self, contexts: IntArray) -> FloatArray:
        total = np.zeros((len(contexts), self.config.embedding), dtype=np.float64)
        for position, table in enumerate(self.embeddings):
            total += table[contexts[:, position]]
        return total

    def logits(self, contexts: IntArray) -> FloatArray:
        return self.context_vectors(contexts) @ self.weights.T + self.biases

    @staticmethod
    def log_softmax(logits: FloatArray) -> FloatArray:
        shifted = logits - logits.max(axis=1, keepdims=True)
        return shifted - np.log(np.exp(shifted).sum(axis=1, keepdims=True))

    def bits_per_row(self, contexts: IntArray, targets: IntArray) -> float:
        log_probabilities = self.log_softmax(self.logits(contexts))
        chosen = log_probabilities[np.arange(len(targets)), targets]
        return float(-chosen.mean() / np.log(2.0))

    def train(
        self,
        contexts: IntArray,
        targets: IntArray,
        *,
        epochs: int,
        learning_rate: float = 0.1,
        batch: int = 256,
        seed: int = 17,
    ) -> list[float]:
        random = np.random.Generator(np.random.PCG64(seed))
        losses: list[float] = []

        for _ in range(epochs):
            order = random.permutation(len(targets))
            for start in range(0, len(order), batch):
                index = order[start : start + batch]
                self._step(contexts[index], targets[index], learning_rate)
            losses.append(self.bits_per_row(contexts, targets))

        return losses

    def _step(
        self, contexts: IntArray, targets: IntArray, learning_rate: float
    ) -> None:
        count = len(targets)
        vectors = self.context_vectors(contexts)
        probabilities = np.exp(self.log_softmax(vectors @ self.weights.T + self.biases))
        probabilities[np.arange(count), targets] -= 1.0
        probabilities /= count

        weight_gradient = probabilities.T @ vectors
        bias_gradient = probabilities.sum(axis=0)
        vector_gradient = probabilities @ self.weights

        self.weights -= learning_rate * weight_gradient
        self.biases -= learning_rate * bias_gradient
        for position, table in enumerate(self.embeddings):
            np.add.at(table, contexts[:, position], -learning_rate * vector_gradient)


class TableBaseline:
    """Interpolated backoff over melody history, optionally split by chord.

    Backoff matters. An unsmoothed table assigns zero probability to any unseen
    continuation, which makes its cross-entropy infinite and the comparison
    meaningless. Interpolating down to the unigram keeps it honest and strong.
    """

    def __init__(self, order: int, *, by_chord: bool = False, weight: float = 0.7):
        self.order = order
        self.by_chord = by_chord
        self.weight = weight
        self.counts: list[dict[tuple[int, ...], NDArray[np.float64]]] = [
            {} for _ in range(order + 1)
        ]

    @property
    def contexts_seen(self) -> int:
        return sum(len(level) for level in self.counts)

    def _keys(self, history: Sequence[int], chord: int) -> list[tuple[int, ...]]:
        keys = []
        for level in range(self.order + 1):
            tail = tuple(history[len(history) - level :]) if level else ()
            keys.append((chord, *tail) if self.by_chord else tail)
        return keys

    def observe(self, history: Sequence[int], chord: int, target: int) -> None:
        for level, key in enumerate(self._keys(history, chord)):
            row = self.counts[level].get(key)
            if row is None:
                row = np.zeros(MELODY_TOKENS, dtype=np.float64)
                self.counts[level][key] = row
            row[target] += 1.0

    def distribution(self, history: Sequence[int], chord: int) -> FloatArray:
        probabilities = np.full(MELODY_TOKENS, 1.0 / MELODY_TOKENS)
        for level, key in enumerate(self._keys(history, chord)):
            row = self.counts[level].get(key)
            if row is None or row.sum() == 0:
                continue
            estimate = row / row.sum()
            # The unigram level is nearly pure. Interpolating it heavily with
            # the uniform floor was a bug: it made the order-0 reference far
            # weaker than an actual unigram, which both flattered the model in
            # the negative control and weakened every table that backs off
            # through it.
            share = self.weight if level else 0.97
            probabilities = share * estimate + (1.0 - share) * probabilities
        return probabilities

    def fit(self, tunes: Sequence[Tune], history_length: int) -> None:
        for tune in tunes:
            history = [PAD] * history_length
            for row in range(tune.rows):
                self.observe(history, tune.chords[row], tune.melody[row])
                history = history[1:] + [tune.melody[row]]

    def bits_per_row(self, tunes: Sequence[Tune], history_length: int) -> float:
        total, rows = 0.0, 0
        for tune in tunes:
            history = [PAD] * history_length
            for row in range(tune.rows):
                probability = self.distribution(history, tune.chords[row])[
                    tune.melody[row]
                ]
                total -= np.log2(max(probability, 1e-12))
                rows += 1
                history = history[1:] + [tune.melody[row]]
        return total / max(1, rows)


@dataclass
class UniformBaseline:
    """The floor. log2(27) bits, by definition."""

    name: str = "uniform"
    bits: float = field(default_factory=lambda: float(np.log2(MELODY_TOKENS)))
