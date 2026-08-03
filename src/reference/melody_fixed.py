"""Fixed-point form of the EXP-010 melody model.

The Mac trains in floating point; the CoCo has none. This quantizes a trained
model to signed bytes and runs inference with integer arithmetic only, so the
two gates that decide whether the 6809 can host it at all can be measured:
the context vector must fit a signed byte, and the score must fit the
accumulator.

The context vector is the sum of every position's embedding. With twenty-two
positions that sum is far larger than any single embedding, which is the
difference from EXP-007's five-position context and the reason this needs
checking rather than assuming.

Scale is chosen rather than fixed. Logits depend only on the product of the
embedding and weight scales, so embeddings can be scaled down and weights up
without changing what the model computes. That freedom is spent on making
overflow unreachable rather than merely unobserved.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from melody_lm import MelodyModel
from numpy.typing import NDArray

IntArray = NDArray[np.int64]

BYTE_LOW = -128
BYTE_HIGH = 127
ACCUMULATOR_LOW = -32768
ACCUMULATOR_HIGH = 32767
TIGHTEN_ATTEMPTS = 12
BIAS_HEADROOM = 0.95

# Scales are set from what is *reachable*, not from what was observed.
#
# Setting them from the training peak leaves the model correct on the data it
# has seen and able to overflow on data it has not. That is the wrong failure
# for this experiment specifically: the demonstration invites a stranger to
# type an opening bar, which is exactly the input most likely to sit outside
# anything in the corpus.
#
# Measured at an observed-peak scale, the context vector reached 104 of 127 on
# held-out data while its reachable bound was 187, and the score's reachable
# bound was 54,604 against an int16 limit of 32,767.


@dataclass
class FixedReport:
    embedding_scale: float
    weight_scale: float
    context_magnitude: int
    score_low: int
    score_high: int
    bits: float

    reachable_context: int = 0
    reachable_score: int = 0

    @property
    def context_fits_byte(self) -> bool:
        """The declared gate is on the reachable bound, not the observed one."""
        return self.reachable_context <= BYTE_HIGH

    @property
    def score_fits_accumulator(self) -> bool:
        return self.reachable_score <= ACCUMULATOR_HIGH


class FixedMelodyModel:
    def __init__(self, model: MelodyModel, contexts: IntArray):
        self.config = model.config

        # Worst-case context: every position contributing its largest embedding
        # at once. No input can exceed this, so scaling to it makes overflow
        # unreachable rather than merely unobserved.
        reachable = float(
            sum(np.abs(table).max(axis=0) for table in model.embeddings).max()
        )
        self.embedding_scale = BYTE_HIGH / max(reachable, 1e-9)

        # Scaling so the float bound is exactly 127 is not enough: rounding
        # each embedding independently can push their sum a few counts over.
        # Tighten until the quantized bound actually holds.
        for _ in range(TIGHTEN_ATTEMPTS):
            self.embeddings = [
                np.clip(
                    np.rint(table * self.embedding_scale), BYTE_LOW, BYTE_HIGH
                ).astype(np.int64)
                for table in model.embeddings
            ]
            if self.reachable_context <= BYTE_HIGH:
                break
            self.embedding_scale *= BYTE_HIGH / (self.reachable_context + 1)

        # Worst-case score is a full-scale context against the widest output
        # row, so the weight scale is set from that rather than from the
        # largest single weight.
        # Reserve part of the accumulator for the bias, which shares the scale
        # and is added on top of the products.
        widest_row = float(np.abs(model.weights).sum(axis=1).max())
        budget = ACCUMULATOR_HIGH * BIAS_HEADROOM
        self.weight_scale = (budget / max(self.reachable_context, 1)) / max(
            widest_row, 1e-9
        )
        # Weights and biases are quantized together, because the bias shares
        # their scale and has to fit the accumulator alongside the products.
        for _ in range(TIGHTEN_ATTEMPTS):
            self.weights = np.clip(
                np.rint(model.weights * self.weight_scale), BYTE_LOW, BYTE_HIGH
            ).astype(np.int64)
            self.product_scale = self.embedding_scale * self.weight_scale
            self.biases = np.clip(
                np.rint(model.biases * self.product_scale),
                ACCUMULATOR_LOW,
                ACCUMULATOR_HIGH,
            ).astype(np.int64)
            if self.reachable_score <= ACCUMULATOR_HIGH:
                break
            # The proportional correction alone can round to no change at all,
            # leaving the loop spinning just over the limit. Cap it so every
            # attempt actually shrinks the scale.
            self.weight_scale *= min(
                0.98, ACCUMULATOR_HIGH / (self.reachable_score + 1)
            )

    def context_vectors(self, contexts: IntArray) -> IntArray:
        total = np.zeros((len(contexts), self.config.embedding), dtype=np.int64)
        for position, table in enumerate(self.embeddings):
            total += table[contexts[:, position]]
        return total

    def scores(self, contexts: IntArray) -> IntArray:
        """Integer scores, exactly as the 6809 would accumulate them."""
        return self.context_vectors(contexts) @ self.weights.T + self.biases

    def bits_per_row(self, contexts: IntArray, targets: IntArray) -> float:
        logits = self.scores(contexts) / self.product_scale
        shifted = logits - logits.max(axis=1, keepdims=True)
        log_probabilities = shifted - np.log(np.exp(shifted).sum(axis=1, keepdims=True))
        chosen = log_probabilities[np.arange(len(targets)), targets]
        return float(-chosen.mean() / np.log(2.0))

    def report(self, contexts: IntArray, targets: IntArray) -> FixedReport:
        vectors = self.context_vectors(contexts)
        scores = vectors @ self.weights.T
        return FixedReport(
            embedding_scale=self.embedding_scale,
            weight_scale=self.weight_scale,
            context_magnitude=int(np.max(np.abs(vectors))),
            score_low=int(scores.min()),
            score_high=int(scores.max()),
            bits=self.bits_per_row(contexts, targets),
            reachable_context=self.reachable_context,
            reachable_score=self.reachable_score,
        )

    @property
    def reachable_context(self) -> int:
        """Largest context vector any input could produce."""
        return int(sum(np.abs(table).max(axis=0) for table in self.embeddings).max())

    @property
    def reachable_score(self) -> int:
        """Largest score a full-scale context could produce, bias included."""
        products = self.reachable_context * np.abs(self.weights).sum(axis=1)
        return int((products + np.abs(self.biases)).max())

    @property
    def parameter_bytes(self) -> int:
        embeddings = sum(int(table.size) for table in self.embeddings)
        return embeddings + int(self.weights.size) + int(self.biases.size)


# exp(-d/32) scaled to a byte, floored at 1 so no token is ever impossible.
# The same table EXP-004 uses, so the two experiments share one approximation.
EXP_LUT = [max(1, round(np.exp(-index / 32.0) * 255)) for index in range(256)]

# The shift sets the temperature. Measured over the holdout, the spread
# between the best score and the rest has a median of 3,400 and a 99th
# percentile of 7,705; a shift of 4 maps that onto the table's useful range
# and works out to a softmax temperature near 1.0, which is what the
# generations were listened to at.
SAMPLE_SHIFT = 4
DRAW_ATTEMPTS = 16


def sample_weights(scores, shift: int = SAMPLE_SHIFT) -> list[int]:
    """Unnormalised probability per token, as bytes."""
    top = int(max(scores))
    return [EXP_LUT[min(255, (top - int(s)) >> shift)] for s in scores]


def draw_token(scores, random, shift: int = SAMPLE_SHIFT) -> int:
    """Draw one token in proportion to its score.

    No division and no 32-bit multiply: the draw is masked to the smallest
    power of two above the total and retried when it lands past the end. That
    is a handful of instructions on a 6809, where a divide is not.
    """
    weights = sample_weights(scores, shift)
    total = sum(weights)

    mask = 1
    while mask < total:
        mask = mask * 2 + 1

    value = total - 1
    for _ in range(DRAW_ATTEMPTS):
        candidate = random.next() & mask
        if candidate < total:
            value = candidate
            break

    running = 0
    for index, weight in enumerate(weights):
        running += weight
        if value < running:
            return index
    return len(weights) - 1
