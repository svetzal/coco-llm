#!/usr/bin/env python3
"""Sweep additive completion models for EXP-007's all-RAM weight budget."""

from __future__ import annotations

import argparse
import json
import sys
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
    load_phrases,
    load_token_sequences,
    make_sequence_examples,
    train_neural_model,
)

DEFAULT_TRAINING = ROOT / "experiments" / "data" / "EXP-006-completion-training.txt"
DEFAULT_HOLDOUT = ROOT / "experiments" / "data" / "EXP-006-completion-holdout.txt"


def comma_separated_integers(text: str) -> list[int]:
    values = [int(value.strip(), 0) for value in text.split(",") if value.strip()]
    if not values or any(value < 1 for value in values):
        raise argparse.ArgumentTypeError("expected positive comma-separated integers")
    return values


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training", type=Path, default=DEFAULT_TRAINING)
    parser.add_argument("--holdout", type=Path, default=DEFAULT_HOLDOUT)
    parser.add_argument(
        "--punctuation",
        action="store_true",
        help="tokenize sentence punctuation instead of splitting only on spaces",
    )
    parser.add_argument(
        "--budgets",
        type=comma_separated_integers,
        default=[32768, 40960, 49152],
    )
    parser.add_argument(
        "--contexts",
        type=comma_separated_integers,
        default=[4, 5, 6],
    )
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--learning-rate", type=float, default=0.01)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--target-vocabulary", type=int, default=255)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def load_sequences(path: Path, *, punctuation: bool) -> list[list[str]]:
    if punctuation:
        return load_token_sequences(path)
    return [phrase.split() for phrase in load_phrases(path)]


def context_magnitudes(model, contexts: np.ndarray) -> tuple[int, int]:
    vectors = np.asarray([model.context_vector(context) for context in contexts])
    observed = int(np.max(np.abs(vectors)))
    position_embeddings = model.position_embeddings.astype(np.int64)
    minimum = np.min(position_embeddings, axis=1).sum(axis=0)
    maximum = np.max(position_embeddings, axis=1).sum(axis=0)
    possible = int(max(np.max(np.abs(minimum)), np.max(np.abs(maximum))))
    return observed, possible


def target_dimensions(
    vocabulary_size: int, context_size: int, budget: int
) -> dict[str, int]:
    embedding = largest_additive_embedding(vocabulary_size, context_size, budget)
    parameters = vocabulary_size * (embedding * (context_size + 1) + 1)
    return {
        "budget": budget,
        "vocabulary": vocabulary_size,
        "context": context_size,
        "embedding": embedding,
        "parameters": parameters,
        "padding": budget - parameters,
        "inference_multiplies": vocabulary_size * embedding,
    }


def main() -> None:
    arguments = parse_arguments()
    training_sequences = load_sequences(
        arguments.training, punctuation=arguments.punctuation
    )
    holdout_sequences = load_sequences(
        arguments.holdout, punctuation=arguments.punctuation
    )
    vocabulary, token_by_text = build_sequence_vocabulary(training_sequences)
    unknown = sorted(
        {
            token
            for sequence in holdout_sequences
            for token in sequence
            if token not in token_by_text
        }
    )
    if unknown:
        raise ValueError(f"holdout contains unknown tokens: {', '.join(unknown)}")

    candidates = []
    for budget in arguments.budgets:
        for context_size in arguments.contexts:
            embedding = largest_additive_embedding(
                len(vocabulary), context_size, budget
            )
            training_contexts, training_targets = make_sequence_examples(
                training_sequences, token_by_text, context_size
            )
            holdout_contexts, holdout_targets = make_sequence_examples(
                holdout_sequences, token_by_text, context_size
            )
            model = AdditiveCompletionModel(
                NeuralConfig(context=context_size, embedding=embedding),
                vocabulary,
            )
            losses = train_neural_model(
                model,
                training_contexts,
                training_targets,
                epochs=arguments.epochs,
                learning_rate=arguments.learning_rate,
                batch_size=arguments.batch_size,
            )
            fixed = model.int8_copy()
            observed, possible = context_magnitudes(fixed, training_contexts)
            candidates.append(
                {
                    "budget": budget,
                    "context": context_size,
                    "embedding": embedding,
                    "parameters": fixed.parameter_count,
                    "padding": budget - fixed.parameter_count,
                    "inference_multiplies": fixed.inference_multiplies,
                    "initial_epoch_loss": losses[0],
                    "final_epoch_loss": losses[-1],
                    "observed_context_magnitude": observed,
                    "possible_context_magnitude": possible,
                    "signed_byte_context": possible <= 127,
                    "metrics": asdict(
                        evaluate(fixed, holdout_contexts, holdout_targets)
                    ),
                }
            )

    target_context = 5
    targets = [
        target_dimensions(
            arguments.target_vocabulary,
            target_context,
            budget,
        )
        for budget in arguments.budgets
    ]
    result = {
        "setup": {
            "training": str(arguments.training),
            "holdout": str(arguments.holdout),
            "punctuation": arguments.punctuation,
            "training_sequences": len(training_sequences),
            "holdout_sequences": len(holdout_sequences),
            "vocabulary_size": len(vocabulary),
            "epochs": arguments.epochs,
        },
        "candidates": candidates,
        "target_255_token_five_context": targets,
    }

    if arguments.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    print(
        f"{len(training_sequences)} training sequences, "
        f"{len(holdout_sequences)} holdout sequences, "
        f"{len(vocabulary)} tokens"
    )
    print()
    print("budget  C   E  params  muls  top-1  top-3  saved  range  8-bit")
    print("------  -  --  ------  ----  -----  -----  -----  -----  -----")
    for candidate in candidates:
        metrics = candidate["metrics"]
        print(
            f"{candidate['budget'] // 1024:>4}K  "
            f"{candidate['context']:>1}  "
            f"{candidate['embedding']:>2}  "
            f"{candidate['parameters']:>6}  "
            f"{candidate['inference_multiplies']:>4}  "
            f"{metrics['top_one_accuracy']:>5.1%}  "
            f"{metrics['top_three_accuracy']:>5.1%}  "
            f"{metrics['keystroke_savings']:>5.1%}  "
            f"{candidate['possible_context_magnitude']:>5}  "
            f"{'yes' if candidate['signed_byte_context'] else 'no':>5}"
        )
    print()
    print("255-token, five-context target dimensions")
    for target in targets:
        print(
            f"{target['budget'] // 1024:>4}K: "
            f"E={target['embedding']}, "
            f"{target['parameters']} parameters, "
            f"{target['padding']} padding, "
            f"{target['inference_multiplies']} multiplies"
        )


if __name__ == "__main__":
    main()
