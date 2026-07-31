"""Online next-move model and table baselines for EXP-008.

The model reuses the EXP-004 fixed-point arithmetic exactly: signed Q4.12
masters, a forward pass over their high bytes as Q4.4, probabilities in units
of 1/256, and a 1/16 learning rate applied as a shift. Sharing that arithmetic
is deliberate, because the 6809 engine that already implements it is the engine
this experiment intends to reuse.

Two things differ from the corpus experiments:

Input and output vocabularies are separate. Context positions may hold bearing
and range tokens, but only the nine move tokens are ever predicted. Separating
them cuts the output layer from twenty rows to nine.

Prediction skips the softmax. Softmax is monotonic, so it cannot change which
logit is largest, and the opponent only needs the largest. Training still needs
it, because the cross-entropy gradient is defined on probabilities. This is the
same distinction EXP-006 recorded for tab completion.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from duel_arena import MOVE_COUNT, TickRecord, input_vocabulary_size
from fixed_token_lm import EXP_LUT, XorShift16, clamp_int16
from numpy.typing import NDArray

IntArray = NDArray[np.int64]


@dataclass(frozen=True)
class MimicConfig:
    """A candidate model.

    `learning_shift` is the right shift applied to parameter updates, so the
    learning rate is 1 / 2**learning_shift. The default of 4 reproduces the
    EXP-004 engine exactly. Smaller shifts learn faster, which matters here
    because a live demonstration has only a few hundred ticks to converge, not
    the twenty passes over a fixed corpus the earlier experiments enjoyed.
    """

    layout: str
    embedding: int = 6
    context: int = 5
    seed: int = 6809
    learning_shift: int = 4


class Predictor(Protocol):
    name: str

    def predict(self, record: TickRecord) -> int: ...

    def observe(self, record: TickRecord, move: int) -> None: ...


class MimicModel:
    """Additive positional-embedding model trained online on a move stream."""

    def __init__(self, config: MimicConfig):
        self.config = config
        self.input_size = input_vocabulary_size(config.layout)
        self.output_size = MOVE_COUNT
        random = XorShift16(config.seed)

        def initial(shape: tuple[int, ...]) -> IntArray:
            result = np.empty(shape, dtype=np.int64)
            for index in np.ndindex(shape):
                result[index] = (random.next() & 0x03FF) - 512
            return result

        self.position_embeddings = initial(
            (config.context, self.input_size, config.embedding)
        )
        self.output_weights = initial((self.output_size, config.embedding))
        self.output_biases = np.zeros(self.output_size, dtype=np.int64)

        self.max_context_magnitude = 0
        self.minimum_score = 0
        self.maximum_score = 0

    @property
    def parameter_count(self) -> int:
        return (
            self.position_embeddings.size
            + self.output_weights.size
            + self.output_biases.size
        )

    @property
    def master_bytes(self) -> int:
        return self.parameter_count * 2

    @property
    def prediction_multiplies(self) -> int:
        return self.output_size * self.config.embedding

    @property
    def training_multiplies(self) -> int:
        # Forward projection, context-error projection, and weight update.
        return 3 * self.output_size * self.config.embedding

    @staticmethod
    def _forward_byte(parameter: int) -> int:
        return parameter >> 8

    def _context_vector(self, context: Sequence[int]) -> IntArray:
        vector = np.zeros(self.config.embedding, dtype=np.int64)
        for position, token in enumerate(context):
            for dimension in range(self.config.embedding):
                vector[dimension] += self._forward_byte(
                    int(self.position_embeddings[position, token, dimension])
                )

        magnitude = int(np.max(np.abs(vector))) if vector.size else 0
        self.max_context_magnitude = max(self.max_context_magnitude, magnitude)
        return vector

    def _logits(self, context_vector: IntArray) -> IntArray:
        logits = np.empty(self.output_size, dtype=np.int64)
        for output in range(self.output_size):
            accumulator = self._forward_byte(int(self.output_biases[output])) << 4
            for dimension in range(self.config.embedding):
                weight = self._forward_byte(int(self.output_weights[output, dimension]))
                accumulator += weight * int(context_vector[dimension])
            self.minimum_score = min(self.minimum_score, accumulator)
            self.maximum_score = max(self.maximum_score, accumulator)
            logits[output] = max(-32768, min(32767, accumulator))
        return logits

    @staticmethod
    def _softmax(logits: IntArray) -> IntArray:
        maximum = int(np.max(logits))
        exponentials = np.empty(len(logits), dtype=np.int64)
        for index, logit in enumerate(logits):
            distance = min(255, max(0, (maximum - int(logit)) >> 3))
            exponentials[index] = EXP_LUT[distance]

        total = int(np.sum(exponentials))
        reciprocal = min(0x1FF, (0x10000 + total // 2) // total)
        probabilities = (exponentials * reciprocal + 0x80) >> 8

        correction = 256 - int(np.sum(probabilities))
        probabilities[int(np.argmax(probabilities))] += correction
        return probabilities

    def predict_context(self, context: Sequence[int]) -> int:
        """Return the highest-scoring move. No softmax; ranking is unchanged."""
        return int(np.argmax(self._logits(self._context_vector(context))))

    def rank_context(self, context: Sequence[int]) -> IntArray:
        return np.argsort(-self._logits(self._context_vector(context)), kind="stable")

    def train_context(self, context: Sequence[int], target: int) -> None:
        shift = self.config.learning_shift
        bias_scale = 4 - shift
        context_vector = self._context_vector(context)
        probabilities = self._softmax(self._logits(context_vector))
        output_error = probabilities.copy()
        output_error[target] -= 256

        context_error = np.zeros(self.config.embedding, dtype=np.int64)
        for dimension in range(self.config.embedding):
            accumulator = 0
            for output in range(self.output_size):
                weight = self._forward_byte(int(self.output_weights[output, dimension]))
                accumulator += (weight * int(output_error[output])) >> shift
            context_error[dimension] = max(-32768, min(32767, accumulator))

        for output in range(self.output_size):
            error = int(output_error[output])
            self.output_biases[output] = clamp_int16(
                int(self.output_biases[output]) - (error << bias_scale)
            )
            for dimension in range(self.config.embedding):
                update = (error * int(context_vector[dimension])) >> shift
                self.output_weights[output, dimension] = clamp_int16(
                    int(self.output_weights[output, dimension]) - update
                )

        for position, token in enumerate(context):
            for dimension in range(self.config.embedding):
                self.position_embeddings[position, token, dimension] = clamp_int16(
                    int(self.position_embeddings[position, token, dimension])
                    - int(context_error[dimension])
                )


class MimicPredictor:
    """Adapts a MimicModel to the prequential predictor interface."""

    def __init__(self, config: MimicConfig, *, name: str | None = None):
        self.model = MimicModel(config)
        self.layout = config.layout
        suffix = "" if config.learning_shift == 4 else f"/S{config.learning_shift}"
        self.name = name or f"model/{config.layout}/E{config.embedding}{suffix}"

    def predict(self, record: TickRecord) -> int:
        return self.model.predict_context(record.context(self.layout))

    def observe(self, record: TickRecord, move: int) -> None:
        self.model.train_context(record.context(self.layout), move)


class UniformBaseline:
    """Guesses uniformly. The floor every other method must clear.

    This deliberately does not use XorShift16. The synthetic players draw from
    that generator, whose 16-bit state has a single orbit, so a uniform guesser
    sharing it can fall into lock-step with a uniformly random player and score
    100%. The baseline is a measurement device rather than a candidate 6809
    implementation, so it is free to use an independent generator, and it must.
    """

    name = "uniform"

    def __init__(self, seed: int = 6809):
        self.random = np.random.Generator(np.random.PCG64(seed))

    def predict(self, record: TickRecord) -> int:
        return int(self.random.integers(MOVE_COUNT))

    def observe(self, record: TickRecord, move: int) -> None:
        return None


class MarginalBaseline:
    """Always predicts the player's most frequent move so far."""

    name = "marginal"

    def __init__(self) -> None:
        self.counts = np.zeros(MOVE_COUNT, dtype=np.int64)

    def predict(self, record: TickRecord) -> int:
        return int(np.argmax(self.counts))

    def observe(self, record: TickRecord, move: int) -> None:
        self.counts[move] += 1


class TableBaseline:
    """An order-N frequency table over recent moves, with backoff.

    Backoff matters. Without it a trigram table is starved early and the
    comparison flatters the model. Backing off to shorter histories, then to
    the marginal distribution, makes this the strongest table the same memory
    can support, which is the comparison the experiment actually needs.
    """

    def __init__(self, order: int, *, name: str | None = None):
        self.order = order
        self.name = name or f"table/order{order}"
        self.tables = [
            np.zeros((MOVE_COUNT**level, MOVE_COUNT), dtype=np.int64)
            for level in range(order + 1)
        ]

    @property
    def counter_cells(self) -> int:
        return sum(int(table.size) for table in self.tables)

    @staticmethod
    def _key(history: Sequence[int], level: int) -> int:
        key = 0
        for move in history[len(history) - level :] if level else ():
            key = key * MOVE_COUNT + move
        return key

    def predict(self, record: TickRecord) -> int:
        for level in range(self.order, -1, -1):
            row = self.tables[level][self._key(record.history, level)]
            if int(row.sum()) > 0:
                return int(np.argmax(row))
        return 0

    def observe(self, record: TickRecord, move: int) -> None:
        for level in range(self.order + 1):
            self.tables[level][self._key(record.history, level)][move] += 1


@dataclass(frozen=True)
class EvaluationResult:
    name: str
    ticks: int
    overall_accuracy: float
    window_accuracy: float


def evaluate_stream(
    stream: Sequence[tuple[TickRecord, int]],
    predictors: Sequence[Predictor],
    *,
    window: int,
) -> list[EvaluationResult]:
    """Score predictors prequentially: predict, then observe, one tick at a time.

    A stream has no natural holdout, so the honest measure is how well each
    method predicts the next move *before* being told it. Scoring the final
    `window` ticks compares methods after all of them have warmed up.
    """
    total_correct = [0] * len(predictors)
    window_correct = [0] * len(predictors)
    window_start = max(0, len(stream) - window)

    for tick, (record, move) in enumerate(stream):
        for index, predictor in enumerate(predictors):
            if predictor.predict(record) == move:
                total_correct[index] += 1
                if tick >= window_start:
                    window_correct[index] += 1
            predictor.observe(record, move)

    scored = len(stream) - window_start
    return [
        EvaluationResult(
            name=predictor.name,
            ticks=len(stream),
            overall_accuracy=total_correct[index] / max(1, len(stream)),
            window_accuracy=window_correct[index] / max(1, scored),
        )
        for index, predictor in enumerate(predictors)
    ]
