#!/usr/bin/env python3
"""Export a real weight update for the shift illustration.

The learning-rate code slide shows eight instructions. This finds a genuine
gradient they operated on during training and records what the four shifts do
to its bits.

Two things matter about which update is chosen. It has to come from
`FixedTokenLanguageModel`, not the floating-point reference, because that is
the model the 6809 matches bit for bit and `gradient >> 4` in its
`train_example` IS the four asra/rorb pairs. And it has to be worth looking at:
a value whose high byte is all zeros shows nothing, so the search prefers a
negative gradient with bits set in both halves, where the sign extension
arriving from the top and the bits crossing from A into B are both visible.

The chosen update is reported with where it came from, because a real value
from an unnamed moment is no better than an invented one.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from fixed_token_lm import FixedTokenLanguageModel  # noqa: E402
from token_lm import (  # noqa: E402
    ModelConfig,
    build_vocabulary,
    load_names,
    make_examples,
)

CORPUS = ROOT / "experiments" / "data" / "EXP-002-tokenized-computer-names.txt"
OUT = ROOT / "presentation" / "deck" / "data" / "shift.json"
SEARCH_EPOCHS = 6
FRACTION_BITS = 12


def interesting(gradient: int) -> bool:
    """Negative, and with bits set in both bytes, or it teaches nothing."""
    if gradient >= 0:
        return False
    word = gradient & 0xFFFF
    high, low = word >> 8, word & 0xFF
    return high not in (0x00, 0xFF) and low not in (0x00, 0xFF)


def main() -> None:
    names = load_names(CORPUS)
    vocabulary, by_text = build_vocabulary(names)
    config = ModelConfig()
    contexts, targets = make_examples(names, by_text, config.context)
    model = FixedTokenLanguageModel(config, vocabulary)

    found = None
    for epoch in range(SEARCH_EPOCHS):
        for index in range(len(targets)):
            context = np.asarray(contexts[index])
            target = int(targets[index])
            vector, probabilities = model._forward(context)
            error = probabilities.copy()
            error[target] -= 256
            for output in range(model.vocabulary_size):
                for dimension in range(config.embedding):
                    gradient = int(error[output]) * int(vector[dimension])
                    if interesting(gradient) and (
                        found is None or gradient < found["gradient"]
                    ):
                        found = {
                            "gradient": gradient,
                            "epoch": epoch,
                            "example": index,
                            "token": vocabulary[target],
                            "weight_of": vocabulary[output],
                            "dimension": dimension,
                            "context_value": int(vector[dimension]),
                            "error": int(error[output]),
                            "weight_before": int(
                                model.output_weights[output, dimension]
                            ),
                        }
            model.train_example(context, target)

    if found is None:
        raise SystemExit("no gradient with bits in both bytes; widen the search")

    # The four asra/rorb pairs, one pair at a time.
    steps, value = [{"value": found["gradient"], "dropped": None}], found["gradient"]
    for _ in range(4):
        steps.append({"value": value >> 1, "dropped": value & 1})
        value >>= 1

    assert steps[-1]["value"] == found["gradient"] >> 4, "four halvings is >> 4"
    assert found["error"] * found["context_value"] == found["gradient"], (
        "the gradient must be the product the machine formed"
    )

    payload = {
        "fraction_bits": FRACTION_BITS,
        "scale": 1 << FRACTION_BITS,
        "source": found,
        "update": steps[-1]["value"],
        "weight_after": found["weight_before"] - steps[-1]["value"],
        "steps": [
            {
                "value": step["value"],
                "bits": format(step["value"] & 0xFFFF, "016b"),
                "dropped": step["dropped"],
            }
            for step in steps
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1) + "\n", encoding="ascii")

    print(
        f"gradient {found['gradient']} from epoch {found['epoch']}, "
        f"{found['weight_of']}'s weight {found['dimension']}: "
        f"error {found['error']} x context {found['context_value']}"
    )
    for step in payload["steps"]:
        bits = step["bits"]
        print(f"  {bits[:8]} {bits[8:]}  {step['value']:>7}")
    print(
        f"weight {found['weight_before']} - {payload['update']} = "
        f"{payload['weight_after']}"
    )


if __name__ == "__main__":
    main()
