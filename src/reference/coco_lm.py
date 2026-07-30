"""Readable floating-point reference model for CoCo LLM.

This implementation values an explicit learning loop over framework
convenience. NumPy supplies matrix arithmetic, but tokenization, forward
propagation, backpropagation, SGD updates, and generation remain visible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

VOCABULARY = "\n -/0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
BOUNDARY = "\n"
FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


@dataclass(frozen=True)
class ModelConfig:
    context: int = 3
    embedding: int = 3
    hidden: int = 6
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
    learned_trigram: bool


def load_names(path: Path) -> list[str]:
    names = [
        line.strip().upper()
        for line in path.read_text(encoding="ascii").splitlines()
        if line.strip()
    ]
    unsupported = sorted(set("".join(names)) - set(VOCABULARY))
    if unsupported:
        raise ValueError(f"Corpus contains unsupported characters: {unsupported}")
    return names


def encode(text: str) -> list[int]:
    token_by_character = {
        character: token for token, character in enumerate(VOCABULARY)
    }
    return [token_by_character[character] for character in text]


def make_examples(names: Sequence[str], context_size: int) -> tuple[IntArray, IntArray]:
    boundary = encode(BOUNDARY)[0]
    contexts: list[list[int]] = []
    targets: list[int] = []

    for name in names:
        context = [boundary] * context_size
        for target in encode(name + BOUNDARY):
            contexts.append(context.copy())
            targets.append(target)
            context = context[1:] + [target]

    return np.asarray(contexts, dtype=np.int64), np.asarray(targets, dtype=np.int64)


class CharacterLanguageModel:
    """One-hidden-layer causal character language model."""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.vocabulary_size = len(VOCABULARY)
        random = np.random.Generator(np.random.PCG64(config.seed))

        self.embeddings = random.normal(
            0.0,
            0.08,
            (self.vocabulary_size, config.embedding),
        )
        self.hidden_weights = random.normal(
            0.0,
            0.08,
            (config.hidden, config.context * config.embedding),
        )
        self.hidden_biases = np.zeros(config.hidden, dtype=np.float64)
        self.output_weights = random.normal(
            0.0,
            0.08,
            (self.vocabulary_size, config.hidden),
        )
        self.output_biases = np.zeros(self.vocabulary_size, dtype=np.float64)

    @property
    def parameters(self) -> tuple[FloatArray, ...]:
        return (
            self.embeddings,
            self.hidden_weights,
            self.hidden_biases,
            self.output_weights,
            self.output_biases,
        )

    @property
    def parameter_count(self) -> int:
        return sum(parameter.size for parameter in self.parameters)

    @property
    def multiplies_per_example(self) -> int:
        input_width = self.config.context * self.config.embedding
        hidden = self.config.hidden
        output = self.vocabulary_size

        forward = hidden * input_width + output * hidden
        backward = (
            output * hidden
            + output * hidden
            + hidden * input_width
            + hidden * input_width
        )
        return forward + backward

    def _forward(
        self,
        context: IntArray,
    ) -> tuple[FloatArray, FloatArray, FloatArray]:
        model_input = self.embeddings[context].reshape(-1)
        hidden = np.tanh(self.hidden_weights @ model_input + self.hidden_biases)
        logits = self.output_weights @ hidden + self.output_biases
        logits -= np.max(logits)
        exponentials = np.exp(logits)
        probabilities = exponentials / np.sum(exponentials)
        return model_input, hidden, probabilities

    def loss(self, contexts: IntArray, targets: IntArray) -> float:
        total = 0.0
        for context, target in zip(contexts, targets, strict=True):
            _, _, probabilities = self._forward(context)
            total -= math.log(max(float(probabilities[target]), 1e-12))
        return total / len(targets)

    def train_example(
        self, context: IntArray, target: int, learning_rate: float
    ) -> float:
        model_input, hidden, probabilities = self._forward(context)
        loss = -math.log(max(float(probabilities[target]), 1e-12))

        output_error = probabilities.copy()
        output_error[target] -= 1.0

        output_weight_gradient = np.outer(output_error, hidden)
        output_bias_gradient = output_error
        hidden_error = self.output_weights.T @ output_error

        hidden_pre_activation_error = hidden_error * (1.0 - hidden * hidden)
        hidden_weight_gradient = np.outer(hidden_pre_activation_error, model_input)
        hidden_bias_gradient = hidden_pre_activation_error
        input_error = self.hidden_weights.T @ hidden_pre_activation_error

        embedding_gradient = np.zeros_like(self.embeddings)
        shaped_input_error = input_error.reshape(
            self.config.context,
            self.config.embedding,
        )
        for position, token in enumerate(context):
            embedding_gradient[token] += shaped_input_error[position]

        self.output_weights -= learning_rate * output_weight_gradient
        self.output_biases -= learning_rate * output_bias_gradient
        self.hidden_weights -= learning_rate * hidden_weight_gradient
        self.hidden_biases -= learning_rate * hidden_bias_gradient
        self.embeddings -= learning_rate * embedding_gradient
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
        seed_text: str = "",
        temperature: float = 0.8,
        max_characters: int = 32,
        random_seed: int = 1,
    ) -> str:
        boundary = encode(BOUNDARY)[0]
        context = [boundary] * self.config.context
        output = seed_text.upper()

        for token in encode(output):
            context = context[1:] + [token]

        random = np.random.Generator(np.random.PCG64(random_seed))
        for _ in range(max_characters - len(output)):
            _, _, probabilities = self._forward(np.asarray(context, dtype=np.int64))
            adjusted = np.log(np.maximum(probabilities, 1e-12)) / temperature
            adjusted -= np.max(adjusted)
            adjusted = np.exp(adjusted)
            adjusted /= np.sum(adjusted)
            token = int(random.choice(self.vocabulary_size, p=adjusted))
            character = VOCABULARY[token]
            if character == BOUNDARY:
                break
            output += character
            context = context[1:] + [token]

        return output

    def checksum(self) -> str:
        digest = hashlib.sha256()
        for parameter in self.parameters:
            digest.update(parameter.astype("<f8", copy=False).tobytes())
        return digest.hexdigest()


def corpus_trigrams(names: Iterable[str]) -> set[str]:
    return {
        name[index : index + 3]
        for name in names
        for index in range(max(0, len(name) - 2))
    }


def assess_samples(
    samples: Sequence[str], names: Sequence[str]
) -> list[SampleAssessment]:
    known_names = set(names)
    trigrams = corpus_trigrams(names)
    assessments: list[SampleAssessment] = []

    for sample in samples:
        learned_trigram = any(
            sample[index : index + 3] in trigrams
            for index in range(max(0, len(sample) - 2))
        )
        name_like = (
            4 <= len(sample) <= 32
            and any(character.isalpha() for character in sample)
            and learned_trigram
        )
        assessments.append(
            SampleAssessment(
                text=sample,
                novel=sample not in known_names,
                name_like=name_like,
                learned_trigram=learned_trigram,
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
    contexts, targets = make_examples(names, config.context)
    model = CharacterLanguageModel(config)
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
        / "EXP-001-computer-names.txt"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=default_corpus)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--context", type=int, default=3)
    parser.add_argument("--embedding", type=int, default=3)
    parser.add_argument("--hidden", type=int, default=6)
    parser.add_argument("--seed", type=int, default=6809)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    config = ModelConfig(
        context=arguments.context,
        embedding=arguments.embedding,
        hidden=arguments.hidden,
        seed=arguments.seed,
    )
    names = load_names(arguments.corpus)
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

    print(f"parameters: {result.parameter_count}")
    print(f"examples: {result.examples}")
    print(f"loss: {result.initial_loss:.4f} -> {result.final_loss:.4f}")
    print(f"elapsed on this Mac: {result.elapsed_seconds:.3f}s")
    print(f"multiplies/example: {result.multiplies_per_example}")
    print(f"checksum: {result.checksum[:16]}")
    print()
    for assessment in assessments:
        status = "novel" if assessment.novel else "copied"
        shape = "name-like" if assessment.name_like else "weak"
        print(f"{assessment.text or '<EMPTY>':32} {status}, {shape}")


if __name__ == "__main__":
    main()
