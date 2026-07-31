#!/usr/bin/env python3
"""Run the frozen EXP-006 pretrained completion comparison."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from completion_lm import (
    AdditiveCompletionModel,
    BackoffNGramPredictor,
    FrequencyPredictor,
    HiddenCompletionModel,
    NeuralConfig,
    build_completion_vocabulary,
    evaluate,
    largest_additive_embedding,
    largest_hidden_width,
    load_phrases,
    make_completion_examples,
    parameter_checksum,
    suggest,
    train_neural_model,
)

DEFAULT_TRAINING = ROOT / "experiments" / "data" / "EXP-006-completion-training.txt"
DEFAULT_HOLDOUT = ROOT / "experiments" / "data" / "EXP-006-completion-holdout.txt"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training", type=Path, default=DEFAULT_TRAINING)
    parser.add_argument("--holdout", type=Path, default=DEFAULT_HOLDOUT)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--learning-rate", type=float, default=0.01)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--budget", type=int, default=8192)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    training_phrases = load_phrases(arguments.training)
    holdout_phrases = load_phrases(arguments.holdout)
    vocabulary, token_by_text = build_completion_vocabulary(training_phrases)
    unknown = sorted(
        {
            word
            for phrase in holdout_phrases
            for word in phrase.split()
            if word not in token_by_text
        }
    )
    if unknown:
        raise ValueError(f"holdout contains unknown words: {', '.join(unknown)}")

    context_size = 4
    training_contexts, training_targets = make_completion_examples(
        training_phrases, token_by_text, context_size
    )
    holdout_contexts, holdout_targets = make_completion_examples(
        holdout_phrases, token_by_text, context_size
    )

    frequency = FrequencyPredictor(vocabulary, training_targets)
    ngram = BackoffNGramPredictor(vocabulary, training_contexts, training_targets)

    additive_embedding = largest_additive_embedding(
        len(vocabulary), context_size, arguments.budget
    )
    additive = AdditiveCompletionModel(
        NeuralConfig(context=context_size, embedding=additive_embedding),
        vocabulary,
    )
    additive_losses = train_neural_model(
        additive,
        training_contexts,
        training_targets,
        epochs=arguments.epochs,
        learning_rate=arguments.learning_rate,
        batch_size=arguments.batch_size,
    )
    additive_quantized = additive.quantized_copy()

    hidden_embedding = 8
    hidden_width = largest_hidden_width(
        len(vocabulary),
        context_size,
        hidden_embedding,
        arguments.budget,
    )
    hidden = HiddenCompletionModel(
        NeuralConfig(
            context=context_size,
            embedding=hidden_embedding,
            hidden=hidden_width,
        ),
        vocabulary,
    )
    hidden_losses = train_neural_model(
        hidden,
        training_contexts,
        training_targets,
        epochs=arguments.epochs,
        learning_rate=arguments.learning_rate,
        batch_size=arguments.batch_size,
    )
    hidden_quantized = hidden.quantized_copy()

    predictors = {
        "frequency": frequency,
        "ngram": ngram,
        "additive_float": additive,
        "additive_q4_4": additive_quantized,
        "hidden_float": hidden,
        "hidden_q4_4": hidden_quantized,
    }
    metrics = {
        name: asdict(evaluate(predictor, holdout_contexts, holdout_targets))
        for name, predictor in predictors.items()
    }
    prompts = [
        ["PRESS", "TAB", "TO"],
        ["LOAD", "THE"],
        ["THE", "COMMODORE"],
        ["THE", "MODEL", "PREDICTS"],
        ["HUMANS", "CHECK", "THE"],
    ]
    samples = {
        " ".join(prompt): suggest(additive_quantized, prompt) for prompt in prompts
    }
    result = {
        "setup": {
            "training_phrases": len(training_phrases),
            "holdout_phrases": len(holdout_phrases),
            "training_examples": len(training_targets),
            "holdout_examples": len(holdout_targets),
            "vocabulary_size": len(vocabulary),
            "weight_budget": arguments.budget,
            "epochs": arguments.epochs,
        },
        "models": {
            "additive": {
                "embedding": additive_embedding,
                "parameters": additive.parameter_count,
                "initial_epoch_loss": additive_losses[0],
                "final_epoch_loss": additive_losses[-1],
                "checksum": parameter_checksum(additive.parameters),
            },
            "hidden": {
                "embedding": hidden_embedding,
                "hidden": hidden_width,
                "parameters": hidden.parameter_count,
                "inference_multiplies": hidden.inference_multiplies,
                "initial_epoch_loss": hidden_losses[0],
                "final_epoch_loss": hidden_losses[-1],
                "checksum": parameter_checksum(hidden.parameters),
            },
            "ngram": {"stored_counts": ngram.stored_counts},
        },
        "metrics": metrics,
        "samples": samples,
    }

    if arguments.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    setup = result["setup"]
    print(
        f"{setup['training_phrases']} training phrases, "
        f"{setup['holdout_phrases']} holdout phrases, "
        f"{setup['vocabulary_size']} tokens"
    )
    print()
    print("model              params   top-1   top-3   saved    loss")
    print("-----------------  -------  ------  ------  -------  ------")
    for name, predictor_metrics in metrics.items():
        parameters = "-"
        if name.startswith("additive"):
            parameters = str(additive.parameter_count)
        elif name.startswith("hidden"):
            parameters = str(hidden.parameter_count)
        print(
            f"{name:17}  {parameters:>7}  "
            f"{predictor_metrics['top_one_accuracy']:6.1%}  "
            f"{predictor_metrics['top_three_accuracy']:6.1%}  "
            f"{predictor_metrics['keystroke_savings']:7.1%}  "
            f"{predictor_metrics['cross_entropy']:6.3f}"
        )
    print()
    print(
        f"selected additive model: E={additive_embedding}, "
        f"{additive.parameter_count} bytes, "
        f"{len(vocabulary) * additive_embedding} multiplies/suggestion"
    )
    for prompt, suggestions in samples.items():
        print(f"{prompt:24} -> {', '.join(suggestions)}")


if __name__ == "__main__":
    main()
