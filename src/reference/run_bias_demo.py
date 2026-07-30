"""Run controlled, integer-only training-data bias comparisons."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from fixed_token_lm import FixedTokenLanguageModel
from token_lm import IntArray, ModelConfig, build_vocabulary, load_names, make_examples


@dataclass(frozen=True)
class BiasRun:
    label: str
    corpus: Path
    epochs: int
    interleaved: bool = False


@dataclass(frozen=True)
class BiasResult:
    label: str
    training_names: int
    examples_per_epoch: int
    epochs: int
    training_updates: int
    initial_loss: float
    final_loss: float
    checksum: str
    first_token_counts: dict[str, int]
    samples: list[str]


def project_root() -> Path:
    return Path(__file__).parents[2]


def configured_runs(root: Path) -> list[BiasRun]:
    data = root / "experiments" / "data"
    return [
        BiasRun("APPLE FAN", data / "EXP-003-apple-fan.txt", 30),
        BiasRun("COMMODORE FAN", data / "EXP-003-commodore-fan.txt", 30),
        BiasRun("TANDY FAN", data / "EXP-003-tandy-fan.txt", 30),
        BiasRun("ALL FANS CONCATENATED", data / "EXP-003-all-fans.txt", 10),
        BiasRun(
            "ALL FANS INTERLEAVED",
            data / "EXP-003-all-fans.txt",
            10,
            interleaved=True,
        ),
    ]


def training_data(
    run: BiasRun,
    token_by_text: dict[str, int],
    context_size: int,
) -> tuple[list[str], IntArray, IntArray]:
    names = load_names(run.corpus)
    if not run.interleaved:
        contexts, targets = make_examples(names, token_by_text, context_size)
        return names, contexts, targets

    data = project_root() / "experiments" / "data"
    fan_files = [
        data / "EXP-003-apple-fan.txt",
        data / "EXP-003-commodore-fan.txt",
        data / "EXP-003-tandy-fan.txt",
    ]
    fan_examples = [
        make_examples(load_names(path), token_by_text, context_size)
        for path in fan_files
    ]
    contexts = np.asarray(
        [
            fan_examples[fan][0][example]
            for example in range(len(fan_examples[0][1]))
            for fan in range(len(fan_examples))
        ],
        dtype=np.int64,
    )
    targets = np.asarray(
        [
            fan_examples[fan][1][example]
            for example in range(len(fan_examples[0][1]))
            for fan in range(len(fan_examples))
        ],
        dtype=np.int64,
    )
    return names, contexts, targets


def run_comparison(sample_count: int = 20) -> list[BiasResult]:
    root = project_root()
    vocabulary_names = load_names(
        root / "experiments" / "data" / "EXP-002-tokenized-computer-names.txt"
    )
    vocabulary_names += load_names(
        root / "experiments" / "data" / "EXP-003-all-fans.txt"
    )
    vocabulary, token_by_text = build_vocabulary(vocabulary_names)
    config = ModelConfig(seed=6809)
    results: list[BiasResult] = []

    for run in configured_runs(root):
        names, contexts, targets = training_data(
            run,
            token_by_text,
            config.context,
        )
        model = FixedTokenLanguageModel(config, vocabulary)
        initial_loss = model.loss(contexts, targets)
        losses = model.train(contexts, targets, epochs=run.epochs)
        samples = [
            model.generate(random_seed=config.seed + index)
            for index in range(sample_count)
        ]
        first_tokens = Counter(sample.split()[0] for sample in samples)
        results.append(
            BiasResult(
                label=run.label,
                training_names=len(names),
                examples_per_epoch=len(targets),
                epochs=run.epochs,
                training_updates=len(targets) * run.epochs,
                initial_loss=initial_loss,
                final_loss=losses[-1],
                checksum=model.checksum(),
                first_token_counts=dict(sorted(first_tokens.items())),
                samples=samples,
            )
        )

    return results


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    results = run_comparison(arguments.samples)

    if arguments.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
        return

    for result in results:
        print(result.label)
        print("=" * len(result.label))
        print(
            f"{result.training_updates} updates, "
            f"loss {result.initial_loss:.4f} -> {result.final_loss:.4f}"
        )
        counts = ", ".join(
            f"{token}={count}" for token, count in result.first_token_counts.items()
        )
        print(f"first tokens: {counts}")
        for sample in result.samples:
            print(f"  {sample}")
        print()


if __name__ == "__main__":
    main()
