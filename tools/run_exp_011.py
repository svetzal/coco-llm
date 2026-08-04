"""Run EXP-011's contextual associative-recall comparison."""

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from associative_attention import (
    AssociativeAttention,
    generate_recall_batch,
    global_lookup_predictions,
    tail_oracle_predictions,
)


def accuracy(predictions: np.ndarray, targets: np.ndarray) -> float:
    return float(np.mean(predictions == targets))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-examples", type=int, default=4096)
    parser.add_argument("--test-examples", type=int, default=4096)
    parser.add_argument("--epochs", type=int, default=400)
    parser.add_argument("--width", type=int, default=5)
    parser.add_argument("--seed", type=int, default=6809)
    parser.add_argument("--training-seed", type=int, default=1101)
    parser.add_argument("--test-seed", type=int, default=1102)
    parser.add_argument("--sweep-seed-start", type=int, default=6809)
    parser.add_argument("--sweep", action="store_true")
    args = parser.parse_args()

    training = generate_recall_batch(
        np.random.default_rng(args.training_seed), args.training_examples
    )
    test = generate_recall_batch(
        np.random.default_rng(args.test_seed), args.test_examples
    )
    model = AssociativeAttention(key_count=16, width=args.width, seed=args.seed)

    initial_accuracy = model.accuracy(test)
    initial_loss = model.slot_cross_entropy_bits(test)
    losses = model.train(training, epochs=args.epochs)
    final_accuracy = model.accuracy(test)
    final_loss = model.slot_cross_entropy_bits(test)
    quantized = model.quantized_copy()

    global_predictions = global_lookup_predictions(training, test, value_count=8)
    print("EXP-011 contextual associative recall")
    print(f"training examples: {len(training):,}")
    print(f"test examples:     {len(test):,}")
    print(f"memory records:    {test.memory_keys.shape[1]}")
    print(f"attention width:   {args.width}")
    print(f"parameters:        {model.parameters}")
    print()
    print("method                         accuracy")
    print(f"chance                          {1 / 8:7.2%}")
    print(
        f"global parameter lookup         {accuracy(global_predictions, test.targets):7.2%}"
    )
    for visible in (1, 2, 4):
        predictions = tail_oracle_predictions(
            training, test, value_count=8, visible_records=visible
        )
        print(
            f"oracle, last {visible} record{'s' if visible > 1 else ' '}          {accuracy(predictions, test.targets):7.2%}"
        )
    print(f"attention, untrained            {initial_accuracy:7.2%}")
    print(f"attention, trained              {final_accuracy:7.2%}")
    print(f"attention, signed Q4.4          {quantized.accuracy(test):7.2%}")
    print()
    print(f"test loss before training: {initial_loss:.3f} bits/record")
    print(f"training loss final epoch: {losses[-1]:.3f} bits/record")
    print(f"test loss after training:  {final_loss:.3f} bits/record")
    print(
        f"Q4.4 test loss:            {quantized.slot_cross_entropy_bits(test):.3f} bits/record"
    )

    if args.sweep:
        print()
        print("width  params  worst float  worst Q4.4  seeds")
        for width in (2, 3, 4, 5, 6, 8):
            float_accuracies = []
            fixed_accuracies = []
            for seed in range(args.sweep_seed_start, args.sweep_seed_start + 5):
                candidate = AssociativeAttention(16, width, seed=seed)
                candidate.train(training, epochs=args.epochs)
                float_accuracies.append(candidate.accuracy(test))
                fixed_accuracies.append(candidate.quantized_copy().accuracy(test))
            print(
                f"{width:5d}  {32 * width:6d}  "
                f"{min(float_accuracies):11.2%}  {min(fixed_accuracies):10.2%}  "
                f"{args.sweep_seed_start}-{args.sweep_seed_start + 4}"
            )


if __name__ == "__main__":
    main()
