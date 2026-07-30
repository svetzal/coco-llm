"""Token-level reference language model for the live CoCo demonstration."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

BOUNDARY = "<END>"
FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


@dataclass(frozen=True)
class ModelConfig:
    context: int = 2
    embedding: int = 3
    seed: int = 6809


@dataclass(frozen=True)
class TrainingResult:
    epochs: int
    examples: int
    elapsed_seconds: float
    initial_loss: float
    final_loss: float
    parameter_count: int
    multiplies_per_example: int
    total_multiplies: int
    checksum: str


@dataclass(frozen=True)
class SampleAssessment:
    text: str
    novel: bool
    name_like: bool


def load_names(path: Path) -> list[str]:
    return [
        line.strip().upper()
        for line in path.read_text(encoding="ascii").splitlines()
        if line.strip()
    ]


def build_vocabulary(names: Sequence[str]) -> tuple[list[str], dict[str, int]]:
    vocabulary = [BOUNDARY] + sorted(
        {token for name in names for token in name.split()}
    )
    return vocabulary, {token: index for index, token in enumerate(vocabulary)}


def make_examples(
    names: Sequence[str],
    token_by_text: dict[str, int],
    context_size: int,
) -> tuple[IntArray, IntArray]:
    contexts: list[list[int]] = []
    targets: list[int] = []

    for name in names:
        context = [token_by_text[BOUNDARY]] * context_size
        sequence = [token_by_text[token] for token in name.split()]
        sequence.append(token_by_text[BOUNDARY])
        for target in sequence:
            contexts.append(context.copy())
            targets.append(target)
            context = context[1:] + [target]

    return np.asarray(contexts, dtype=np.int64), np.asarray(targets, dtype=np.int64)


class TokenLanguageModel:
    """Additive positional-embedding language model with a softmax output."""

    def __init__(self, config: ModelConfig, vocabulary: Sequence[str]):
        self.config = config
        self.vocabulary = list(vocabulary)
        self.token_by_text = {
            token: index for index, token in enumerate(self.vocabulary)
        }
        self.vocabulary_size = len(self.vocabulary)
        random = np.random.Generator(np.random.PCG64(config.seed))

        self.position_embeddings = random.normal(
            0.0,
            0.08,
            (config.context, self.vocabulary_size, config.embedding),
        )
        self.output_weights = random.normal(
            0.0,
            0.08,
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

    @property
    def multiplies_per_example(self) -> int:
        # One output projection in the forward pass, one output-weight update,
        # and one projection back into the context representation.
        return 3 * self.vocabulary_size * self.config.embedding

    def _forward(self, context: IntArray) -> tuple[FloatArray, FloatArray]:
        context_vector = np.zeros(self.config.embedding, dtype=np.float64)
        for position, token in enumerate(context):
            context_vector += self.position_embeddings[position, token]

        logits = self.output_weights @ context_vector + self.output_biases
        logits -= np.max(logits)
        exponentials = np.exp(logits)
        probabilities = exponentials / np.sum(exponentials)
        return context_vector, probabilities

    def loss(self, contexts: IntArray, targets: IntArray) -> float:
        total = 0.0
        for context, target in zip(contexts, targets, strict=True):
            _, probabilities = self._forward(context)
            total -= math.log(max(float(probabilities[target]), 1e-12))
        return total / len(targets)

    def train_example(
        self, context: IntArray, target: int, learning_rate: float
    ) -> float:
        context_vector, probabilities = self._forward(context)
        loss = -math.log(max(float(probabilities[target]), 1e-12))

        output_error = probabilities.copy()
        output_error[target] -= 1.0
        context_error = self.output_weights.T @ output_error
        output_weight_gradient = np.outer(output_error, context_vector)

        self.output_weights -= learning_rate * output_weight_gradient
        self.output_biases -= learning_rate * output_error
        for position, token in enumerate(context):
            self.position_embeddings[position, token] -= learning_rate * context_error

        return loss

    def train(
        self,
        contexts: IntArray,
        targets: IntArray,
        *,
        epochs: int,
        learning_rate: float,
    ) -> list[float]:
        losses: list[float] = []
        for _ in range(epochs):
            total = 0.0
            for context, target in zip(contexts, targets, strict=True):
                total += self.train_example(context, int(target), learning_rate)
            losses.append(total / len(targets))
        return losses

    def generate(
        self,
        *,
        temperature: float = 0.7,
        max_tokens: int = 6,
        minimum_tokens: int = 2,
        random_seed: int = 1,
    ) -> str:
        boundary = self.token_by_text[BOUNDARY]
        context = [boundary] * self.config.context
        output: list[str] = []
        random = np.random.Generator(np.random.PCG64(random_seed))

        for _ in range(max_tokens):
            _, probabilities = self._forward(np.asarray(context, dtype=np.int64))
            adjusted = np.log(np.maximum(probabilities, 1e-12)) / temperature
            adjusted -= np.max(adjusted)
            adjusted = np.exp(adjusted)
            if len(output) < minimum_tokens:
                adjusted[boundary] = 0.0
            adjusted /= np.sum(adjusted)

            token = int(random.choice(self.vocabulary_size, p=adjusted))
            if token == boundary:
                break
            output.append(self.vocabulary[token])
            context = context[1:] + [token]

        return " ".join(output)

    def checksum(self) -> str:
        digest = hashlib.sha256()
        for parameter in self.parameters:
            digest.update(parameter.astype("<f8", copy=False).tobytes())
        return digest.hexdigest()


def assess_samples(
    samples: Sequence[str],
    names: Sequence[str],
) -> list[SampleAssessment]:
    known_names = set(names)
    first_tokens = {name.split()[0] for name in names}
    assessments: list[SampleAssessment] = []

    for sample in samples:
        tokens = sample.split()
        assessments.append(
            SampleAssessment(
                text=sample,
                novel=sample not in known_names,
                name_like=2 <= len(tokens) <= 4 and tokens[0] in first_tokens,
            )
        )

    return assessments


def run_training(
    names: Sequence[str],
    config: ModelConfig,
    *,
    epochs: int,
    learning_rate: float,
    sample_count: int,
    temperature: float,
) -> tuple[TrainingResult, list[float], list[SampleAssessment]]:
    vocabulary, token_by_text = build_vocabulary(names)
    contexts, targets = make_examples(names, token_by_text, config.context)
    model = TokenLanguageModel(config, vocabulary)
    initial_loss = model.loss(contexts, targets)

    started = time.perf_counter()
    losses = model.train(
        contexts,
        targets,
        epochs=epochs,
        learning_rate=learning_rate,
    )
    elapsed = time.perf_counter() - started

    samples = [
        model.generate(
            temperature=temperature,
            random_seed=config.seed + sample_number,
        )
        for sample_number in range(sample_count)
    ]
    assessments = assess_samples(samples, names)
    result = TrainingResult(
        epochs=epochs,
        examples=len(targets),
        elapsed_seconds=elapsed,
        initial_loss=initial_loss,
        final_loss=losses[-1],
        parameter_count=model.parameter_count,
        multiplies_per_example=model.multiplies_per_example,
        total_multiplies=model.multiplies_per_example * len(targets) * epochs,
        checksum=model.checksum(),
    )
    return result, losses, assessments


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
    parser.add_argument("--learning-rate", type=float, default=0.0625)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--context", type=int, default=2)
    parser.add_argument("--embedding", type=int, default=3)
    parser.add_argument("--seed", type=int, default=6809)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    config = ModelConfig(
        context=arguments.context,
        embedding=arguments.embedding,
        seed=arguments.seed,
    )
    names = load_names(arguments.corpus)
    vocabulary, _ = build_vocabulary(names)
    result, losses, assessments = run_training(
        names,
        config,
        epochs=arguments.epochs,
        learning_rate=arguments.learning_rate,
        sample_count=arguments.samples,
        temperature=arguments.temperature,
    )
    payload = {
        "config": asdict(config),
        "corpus_names": len(names),
        "vocabulary": vocabulary,
        "result": asdict(result),
        "epoch_losses": losses,
        "assessments": [asdict(assessment) for assessment in assessments],
        "novel_rate": sum(item.novel for item in assessments) / len(assessments),
        "name_like_rate": sum(item.name_like for item in assessments)
        / len(assessments),
    }

    if arguments.json:
        print(json.dumps(payload, indent=2))
        return

    print(f"vocabulary: {len(vocabulary)} tokens")
    print(f"parameters: {result.parameter_count}")
    print(f"examples: {result.examples}")
    print(f"loss: {result.initial_loss:.4f} -> {result.final_loss:.4f}")
    print(f"elapsed on this Mac: {result.elapsed_seconds:.3f}s")
    print(f"multiplies/example: {result.multiplies_per_example}")
    print(f"total multiplies: {result.total_multiplies}")
    print(f"checksum: {result.checksum[:16]}")
    print()
    for assessment in assessments:
        status = "novel" if assessment.novel else "copied"
        shape = "name-like" if assessment.name_like else "weak"
        print(f"{assessment.text:32} {status}, {shape}")


if __name__ == "__main__":
    main()
