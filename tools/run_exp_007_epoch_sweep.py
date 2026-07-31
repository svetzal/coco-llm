#!/usr/bin/env python3
"""Measure how EXP-007 changes as its Mac training epoch budget grows."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from completion_lm import (
    AdditiveCompletionModel,
    NeuralConfig,
    build_sequence_vocabulary,
    evaluate,
    largest_additive_embedding,
    load_token_sequences,
    make_sequence_examples,
    train_neural_model,
)
from token_lm import BOUNDARY

DEFAULT_TRAINING = ROOT / "experiments" / "data" / "EXP-007-sentence-training.txt"
DEFAULT_HOLDOUT = ROOT / "experiments" / "data" / "EXP-007-sentence-holdout.txt"
DEFAULT_OUTPUT = ROOT / "build" / "exp007" / "epoch-sweep.json"
MODEL_BYTES = 32768
CONTEXT_SIZE = 5
TERMINAL_PUNCTUATION = frozenset({".", "?", "!"})
DISPLAY_PUNCTUATION = frozenset({".", ",", "?", "!", ":", ";"})


def comma_separated_epochs(text: str) -> list[int]:
    epochs = sorted({int(value.strip()) for value in text.split(",") if value.strip()})
    if not epochs or epochs[0] < 1:
        raise argparse.ArgumentTypeError("epochs must be positive integers")
    return epochs


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training", type=Path, default=DEFAULT_TRAINING)
    parser.add_argument("--holdout", type=Path, default=DEFAULT_HOLDOUT)
    parser.add_argument(
        "--epochs",
        type=comma_separated_epochs,
        default=[1, 2, 5, 10, 20, 40, 80, 160],
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def sentence_boundary_contexts(
    contexts: np.ndarray,
    targets: np.ndarray,
    vocabulary: list[str],
    boundary: int,
) -> list[np.ndarray]:
    return [
        context
        for context, target in zip(contexts, targets, strict=True)
        if int(target) == boundary
        and vocabulary[int(context[-1])] in TERMINAL_PUNCTUATION
    ]


def boundary_behavior(model, contexts: list[np.ndarray]) -> dict[str, object]:
    boundary = model.token_by_text[BOUNDARY]
    boundary_first = 0
    punctuation_fallbacks = 0
    fallback_counts: Counter[str] = Counter()

    for context in contexts:
        scores = model.integer_scores(context)
        ranking = np.argsort(-scores, kind="stable")
        boundary_first += int(int(ranking[0]) == boundary)
        fallback = next(int(index) for index in ranking if int(index) != boundary)
        fallback_token = model.vocabulary[fallback]
        fallback_counts[fallback_token] += 1
        punctuation_fallbacks += int(fallback_token in DISPLAY_PUNCTUATION)

    count = len(contexts)
    return {
        "contexts": count,
        "boundary_top_one_rate": boundary_first / count,
        "visible_fallback_punctuation_rate": punctuation_fallbacks / count,
        "visible_fallbacks": fallback_counts.most_common(),
    }


def main() -> None:
    arguments = parse_arguments()
    training_sequences = load_token_sequences(arguments.training)
    holdout_sequences = load_token_sequences(arguments.holdout)
    vocabulary, token_by_text = build_sequence_vocabulary(training_sequences)
    training_contexts, training_targets = make_sequence_examples(
        training_sequences, token_by_text, CONTEXT_SIZE
    )
    holdout_contexts, holdout_targets = make_sequence_examples(
        holdout_sequences, token_by_text, CONTEXT_SIZE
    )
    boundary = token_by_text[BOUNDARY]
    boundary_contexts = sentence_boundary_contexts(
        holdout_contexts,
        holdout_targets,
        vocabulary,
        boundary,
    )
    embedding = largest_additive_embedding(len(vocabulary), CONTEXT_SIZE, MODEL_BYTES)

    results = []
    for epochs in arguments.epochs:
        model = AdditiveCompletionModel(
            NeuralConfig(context=CONTEXT_SIZE, embedding=embedding), vocabulary
        )
        losses = train_neural_model(
            model,
            training_contexts,
            training_targets,
            epochs=epochs,
            learning_rate=0.01,
            batch_size=32,
        )
        full_metrics = evaluate(model, holdout_contexts, holdout_targets)
        fixed = model.int8_copy(fractional_bits=2, value_bits=4)
        fixed_metrics = evaluate(fixed, holdout_contexts, holdout_targets)
        boundary_result = boundary_behavior(fixed, boundary_contexts)
        boundary_result["by_terminal_token"] = {
            token: boundary_behavior(
                fixed,
                [
                    context
                    for context in boundary_contexts
                    if vocabulary[int(context[-1])] == token
                ],
            )
            for token in sorted(TERMINAL_PUNCTUATION)
        }
        results.append(
            {
                "epochs": epochs,
                "training_loss": losses[-1],
                "full_precision": asdict(full_metrics),
                "q2_2": asdict(fixed_metrics),
                "sentence_boundary": boundary_result,
            }
        )

    report = {
        "experiment": "EXP-007 epoch sweep",
        "training_sentences": len(training_sequences),
        "holdout_sentences": len(holdout_sequences),
        "vocabulary_size": len(vocabulary),
        "context": CONTEXT_SIZE,
        "embedding": embedding,
        "parameters": len(vocabulary) * (embedding * (CONTEXT_SIZE + 1) + 1),
        "results": results,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )

    print(
        "epochs  loss   float top3  Q2.2 top1  Q2.2 top3  saved  END first  fallback punct"
    )
    print(
        "------  -----  ----------  ---------  ---------  -----  ---------  --------------"
    )
    for result in results:
        full = result["full_precision"]
        fixed = result["q2_2"]
        behavior = result["sentence_boundary"]
        print(
            f"{result['epochs']:>6}  "
            f"{result['training_loss']:>5.3f}  "
            f"{full['top_three_accuracy']:>10.1%}  "
            f"{fixed['top_one_accuracy']:>9.1%}  "
            f"{fixed['top_three_accuracy']:>9.1%}  "
            f"{fixed['keystroke_savings']:>5.1%}  "
            f"{behavior['boundary_top_one_rate']:>9.1%}  "
            f"{behavior['visible_fallback_punctuation_rate']:>14.1%}"
        )
    print()
    print(f"wrote {arguments.output}")


if __name__ == "__main__":
    main()
