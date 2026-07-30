"""Integer-only reference for the 290-parameter CoCo token model.

Parameter masters use signed Q4.12. The forward pass consumes their high bytes
as signed Q4.4 values, preserving eight low residual bits for small updates.
Probabilities and output errors use units of 1/256.
"""

from __future__ import annotations

import argparse
import hashlib
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from token_lm import (
    BOUNDARY,
    ModelConfig,
    assess_samples,
    build_vocabulary,
    load_names,
    make_examples,
)

IntArray = NDArray[np.int64]
EXP_LUT = np.asarray(
    [max(1, round(math.exp(-index / 32.0) * 255)) for index in range(256)],
    dtype=np.int64,
)


def clamp_int16(value: int) -> int:
    return max(-32768, min(32767, value))


class XorShift16:
    def __init__(self, seed: int):
        self.state = seed & 0xFFFF
        if self.state == 0:
            self.state = 1

    def next(self) -> int:
        value = self.state
        value ^= (value << 7) & 0xFFFF
        value ^= value >> 9
        value ^= (value << 8) & 0xFFFF
        self.state = value & 0xFFFF
        return self.state


@dataclass(frozen=True)
class FixedTrainingResult:
    epochs: int
    examples: int
    initial_loss: float
    final_loss: float
    parameter_count: int
    total_multiplies: int
    checksum: str


class FixedTokenLanguageModel:
    def __init__(self, config: ModelConfig, vocabulary: Sequence[str]):
        self.config = config
        self.vocabulary = list(vocabulary)
        self.token_by_text = {
            token: index for index, token in enumerate(self.vocabulary)
        }
        self.vocabulary_size = len(self.vocabulary)
        random = XorShift16(config.seed)

        def initial(shape: tuple[int, ...]) -> IntArray:
            result = np.empty(shape, dtype=np.int64)
            for index in np.ndindex(shape):
                result[index] = (random.next() & 0x03FF) - 512
            return result

        self.position_embeddings = initial(
            (config.context, self.vocabulary_size, config.embedding)
        )
        self.output_weights = initial((self.vocabulary_size, config.embedding))
        self.output_biases = np.zeros(self.vocabulary_size, dtype=np.int64)

    @property
    def parameters(self) -> tuple[IntArray, ...]:
        return (
            self.position_embeddings,
            self.output_weights,
            self.output_biases,
        )

    @property
    def parameter_count(self) -> int:
        return sum(parameter.size for parameter in self.parameters)

    @property
    def multiplies_per_example(self) -> int:
        return 3 * self.vocabulary_size * self.config.embedding

    @staticmethod
    def _forward_byte(parameter: int) -> int:
        return parameter >> 8

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
        winner = int(np.argmax(probabilities))
        probabilities[winner] += correction
        return probabilities

    def _forward(self, context: IntArray) -> tuple[IntArray, IntArray]:
        context_vector = np.zeros(self.config.embedding, dtype=np.int64)
        for position, token in enumerate(context):
            for dimension in range(self.config.embedding):
                context_vector[dimension] += self._forward_byte(
                    int(self.position_embeddings[position, token, dimension])
                )

        logits = np.empty(self.vocabulary_size, dtype=np.int64)
        for output in range(self.vocabulary_size):
            accumulator = self._forward_byte(int(self.output_biases[output])) << 4
            for dimension in range(self.config.embedding):
                weight = self._forward_byte(int(self.output_weights[output, dimension]))
                accumulator += weight * int(context_vector[dimension])
            logits[output] = max(-32768, min(32767, accumulator))

        return context_vector, self._softmax(logits)

    def loss(self, contexts: IntArray, targets: IntArray) -> float:
        total = 0.0
        for context, target in zip(contexts, targets, strict=True):
            _, probabilities = self._forward(context)
            probability = max(1, int(probabilities[target])) / 256.0
            total -= math.log(probability)
        return total / len(targets)

    def train_example(self, context: IntArray, target: int) -> None:
        context_vector, probabilities = self._forward(context)
        output_error = probabilities.copy()
        output_error[target] -= 256

        context_error = np.zeros(self.config.embedding, dtype=np.int64)
        for dimension in range(self.config.embedding):
            accumulator = 0
            for output in range(self.vocabulary_size):
                weight = self._forward_byte(int(self.output_weights[output, dimension]))
                accumulator += (weight * int(output_error[output])) >> 4
            context_error[dimension] = max(-32768, min(32767, accumulator))

        for output in range(self.vocabulary_size):
            error = int(output_error[output])
            self.output_biases[output] = clamp_int16(
                int(self.output_biases[output]) - error
            )
            for dimension in range(self.config.embedding):
                gradient_q4_12 = error * int(context_vector[dimension])
                update = gradient_q4_12 >> 4
                self.output_weights[output, dimension] = clamp_int16(
                    int(self.output_weights[output, dimension]) - update
                )

        for position, token in enumerate(context):
            for dimension in range(self.config.embedding):
                self.position_embeddings[position, token, dimension] = clamp_int16(
                    int(self.position_embeddings[position, token, dimension])
                    - int(context_error[dimension])
                )

    def train(
        self, contexts: IntArray, targets: IntArray, *, epochs: int
    ) -> list[float]:
        losses: list[float] = []
        for _ in range(epochs):
            for context, target in zip(contexts, targets, strict=True):
                self.train_example(context, int(target))
            losses.append(self.loss(contexts, targets))
        return losses

    def generate(
        self,
        *,
        max_tokens: int = 6,
        minimum_tokens: int = 2,
        random_seed: int,
    ) -> str:
        boundary = self.token_by_text[BOUNDARY]
        context = [boundary] * self.config.context
        output: list[str] = []
        random = XorShift16(random_seed)

        for _ in range(max_tokens):
            _, probabilities = self._forward(np.asarray(context, dtype=np.int64))
            if len(output) < minimum_tokens:
                probabilities = probabilities.copy()
                removed = int(probabilities[boundary])
                probabilities[boundary] = 0
                probabilities[int(np.argmax(probabilities))] += removed

            draw = random.next() & 0xFF
            cumulative = 0
            token = boundary
            for candidate, probability in enumerate(probabilities):
                cumulative += int(probability)
                if draw < cumulative:
                    token = candidate
                    break

            if token == boundary:
                break
            output.append(self.vocabulary[token])
            context = context[1:] + [token]

        return " ".join(output)

    def checksum(self) -> str:
        digest = hashlib.sha256()
        for parameter in self.parameters:
            digest.update(parameter.astype(">i2", copy=False).tobytes())
        return digest.hexdigest()


def parse_arguments() -> argparse.Namespace:
    default_corpus = (
        Path(__file__).parents[2]
        / "experiments"
        / "data"
        / "EXP-002-tokenized-computer-names.txt"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=default_corpus)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--seed", type=int, default=6809)
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    names = load_names(arguments.corpus)
    vocabulary, token_by_text = build_vocabulary(names)
    config = ModelConfig(seed=arguments.seed)
    contexts, targets = make_examples(names, token_by_text, config.context)
    model = FixedTokenLanguageModel(config, vocabulary)
    initial_loss = model.loss(contexts, targets)
    losses = model.train(contexts, targets, epochs=arguments.epochs)
    samples = [
        model.generate(random_seed=config.seed + index)
        for index in range(arguments.samples)
    ]
    assessments = assess_samples(samples, names)
    result = FixedTrainingResult(
        epochs=arguments.epochs,
        examples=len(targets),
        initial_loss=initial_loss,
        final_loss=losses[-1],
        parameter_count=model.parameter_count,
        total_multiplies=(
            model.multiplies_per_example * len(targets) * arguments.epochs
        ),
        checksum=model.checksum(),
    )

    print(f"vocabulary: {len(vocabulary)} tokens")
    print(f"parameters: {result.parameter_count}")
    print(f"examples: {result.examples}")
    print(f"loss: {result.initial_loss:.4f} -> {result.final_loss:.4f}")
    print(f"total multiplies: {result.total_multiplies}")
    print(f"checksum: {result.checksum[:16]}")
    print()
    for assessment in assessments:
        status = "novel" if assessment.novel else "copied"
        shape = "name-like" if assessment.name_like else "weak"
        print(f"{assessment.text:32} {status}, {shape}")


if __name__ == "__main__":
    main()
