#!/usr/bin/env python3
"""Export EXP-005's prompted completions for the deck.

The block 4 slide claims a prompt changes the completion while the model does
not change. That is a before-and-after claim, so it needs a before: the same
model, same seed, same greedy decoding, asked with no prompt at all. Everything
here comes from one trained model in one run, so the "same model" part of the
claim is true by construction rather than by assertion.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from fixed_token_lm import FixedTokenLanguageModel  # noqa: E402
from token_lm import (  # noqa: E402
    ModelConfig,
    build_vocabulary,
    load_names,
    make_examples,
)

CORPUS = ROOT / "experiments" / "data" / "EXP-005-marketing-language.txt"
FIRST_CORPUS = ROOT / "experiments" / "data" / "EXP-002-tokenized-computer-names.txt"
PROMPTS = ROOT / "experiments" / "data" / "EXP-005-prompts.txt"
OUT = ROOT / "presentation" / "deck" / "data" / "prompts.json"
EPOCHS = 80


def main() -> None:
    phrases = load_names(CORPUS)
    vocabulary, by_text = build_vocabulary(phrases)
    config = ModelConfig(seed=6809)
    contexts, targets = make_examples(phrases, by_text, config.context)

    model = FixedTokenLanguageModel(config, vocabulary)
    losses = model.train(contexts, targets, epochs=EPOCHS)

    def ask(prompt: str | None) -> str:
        return model.generate(
            random_seed=config.seed,
            minimum_tokens=0,
            greedy=True,
            **({"prompt": prompt} if prompt else {}),
        )

    prompts = [line.strip() for line in PROMPTS.read_text().splitlines() if line.strip()]
    # The block 4 intro slide shows this vocabulary against the first model's,
    # so both lists are exported the same way the models build them.
    first_vocabulary, _ = build_vocabulary(load_names(FIRST_CORPUS))

    # The same MUL-floor arithmetic the deck's Why three? figure uses, at
    # this model's vocabulary and epoch count. A floor, not a runtime.
    mul_cycles = 11
    clock_hz = 894_886
    per_example = 3 * len(vocabulary) * config.embedding
    total_multiplies = per_example * len(targets) * EPOCHS
    budget = {
        "per_example": per_example,
        "multiplies": total_multiplies,
        "floor_seconds": round(total_multiplies * mul_cycles / clock_hz, 1),
        "weight_bytes": model.parameter_count * 2,
    }
    payload = {
        "parameters": model.parameter_count,
        "vocabulary": len(vocabulary),
        "epochs": EPOCHS,
        "examples": len(targets),
        "context": config.context,
        "embedding": config.embedding,
        "budget": budget,
        "tokens": list(vocabulary),
        "first_model_tokens": list(first_vocabulary),
        "final_loss": round(losses[-1], 3),
        "checksum": model.checksum()[:16],
        # The before. Same weights, same seed, same decoding, no prompt.
        "unprompted": ask(None),
        # Whether each completion reproduces a corpus line verbatim - the
        # experiment's called shot expected most to (the model is overfit on
        # purpose) and at least one to blend instead.
        "completions": [
            {
                "prompt": prompt,
                "completion": (completion := ask(prompt)),
                "verbatim": f"{prompt} {completion}" in phrases,
            }
            for prompt in prompts
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1) + "\n", encoding="ascii")
    print(f"{payload['parameters']} parameters, checksum {payload['checksum']}")
    print(f"  no prompt -> {payload['unprompted']}")
    for item in payload["completions"]:
        print(f"  {item['prompt']:<14} -> {item['completion']}")


if __name__ == "__main__":
    main()
