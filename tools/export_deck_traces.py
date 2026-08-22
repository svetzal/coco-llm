#!/usr/bin/env python3
"""Export real model traces for the deck's figures.

The copy discipline says no sample output goes on a slide unless it came from a
real run. A figure is sample output. So the numbers an animation shows - the
token identifiers, the context vector, the logits, the weight that moves when
the model is corrected - are taken from the reference implementation here and
written to JSON, rather than being invented to make a diagram look tidy.

This costs almost nothing and buys two things. The figure cannot drift away
from the model, and when someone in the front row asks whether those are the
real numbers, the answer is yes.

Three traces, matching the blocks that need them:

  vocabulary  block 2. What the machine thinks a word is, and the sliding
              window that turns one name into several training examples.
  step        block 3. One training step on one example, before and after,
              including which weights moved and by how much.
  loop        block 3. Loss per epoch, and what the model generates at
              checkpoints along the way.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from token_lm import (  # noqa: E402
    ModelConfig,
    TokenLanguageModel,
    build_vocabulary,
    load_names,
    make_examples,
)

CORPUS = ROOT / "experiments" / "data" / "EXP-002-tokenized-computer-names.txt"
OUT = ROOT / "presentation" / "deck" / "data" / "traces.json"

# The name the whole talk keeps returning to.
FOCUS = "COMMODORE AMIGA"
LEARNING_RATE = 0.35
EPOCHS = 60
CHECKPOINTS = (0, 1, 5, 20, EPOCHS)


def round_all(value, places=4):
    if isinstance(value, (list, tuple)):
        return [round_all(v, places) for v in value]
    return round(float(value), places)


def main() -> None:
    names = load_names(CORPUS)
    vocabulary, token_by_text = build_vocabulary(names)
    config = ModelConfig()
    contexts, targets = make_examples(names, token_by_text, config.context)

    # --- block 2: what a word is, and where examples come from ---------------
    focus_tokens = FOCUS.split()
    boundary = vocabulary[0]
    walk = []
    context = [0] * config.context
    for token in [*focus_tokens, boundary]:
        target = token_by_text[token]
        walk.append(
            {
                "context": list(context),
                "context_text": [vocabulary[i] for i in context],
                "target": target,
                "target_text": vocabulary[target],
            }
        )
        context = context[1:] + [target]

    vocabulary_trace = {
        "vocabulary": vocabulary,
        "focus": FOCUS,
        "focus_tokens": [
            {"text": t, "id": token_by_text[t]} for t in focus_tokens
        ],
        "boundary": boundary,
        "walk": walk,
        "names": len(names),
        "examples": int(len(targets)),
    }

    # --- block 3: one training step, before and after ------------------------
    model = TokenLanguageModel(config, vocabulary)
    example = walk[1]  # COMMODORE -> AMIGA, the one the talk uses
    ctx = np.asarray(example["context"], dtype=np.int64)
    target = example["target"]

    # Where the three numbers come from. The context vector is not computed,
    # it is looked up: every (slot, token) pair owns a stored row, and the
    # vector is those rows added together. Export the rows so the figure can
    # show the addition rather than assert its result.
    lookups = [
        {
            "slot": position + 1,
            "text": example["context_text"][position],
            "row": round_all(model.position_embeddings[position, token].tolist()),
        }
        for position, token in enumerate(ctx)
    ]
    # The same word in the other slot owns a different row. That is the whole
    # of what "positional" means here, and it is why COMMODORE AMIGA and
    # AMIGA COMMODORE are not the same context.
    other_slot = {
        "text": example["context_text"][1],
        "slot": 1,
        "row": round_all(model.position_embeddings[0, ctx[1]].tolist()),
    }

    # A figure shows rounded values, and rounded addends do not always add up
    # to the rounded sum: here -0.0187 + -0.0266 displays as -0.0453 while the
    # true sum rounds to -0.0454. Someone in the front row will add them. So
    # the figure's sum is the sum OF THE DISPLAYED ROWS, which keeps it
    # internally consistent and still within 1e-4 of what the model holds.
    # The model's own value is exported separately and is what the logits use.
    vector_display = [
        round(sum(l["row"][i] for l in lookups), 4) for i in range(config.embedding)
    ]

    vector_before, probabilities_before = model._forward(ctx)
    logits_before = model.output_weights @ vector_before + model.output_biases
    weights_before = model.output_weights[target].copy()
    ranked = np.argsort(-probabilities_before)[:5]

    loss = model.train_example(ctx, target, LEARNING_RATE)

    vector_after, probabilities_after = model._forward(ctx)
    weights_after = model.output_weights[target].copy()

    error = probabilities_before.copy()
    error[target] -= 1.0

    step_trace = {
        "context_text": example["context_text"],
        "target_text": example["target_text"],
        "target": target,
        "learning_rate": LEARNING_RATE,
        "lookups": lookups,
        "vector_display": vector_display,
        "other_slot": other_slot,
        "vector_before": round_all(vector_before.tolist()),
        "vector_after": round_all(vector_after.tolist()),
        "logits": round_all(logits_before.tolist(), 3),
        "probabilities_before": round_all(probabilities_before.tolist(), 5),
        "probabilities_after": round_all(probabilities_after.tolist(), 5),
        "top_before": [
            {
                "text": vocabulary[i],
                "p": round(float(probabilities_before[i]), 5),
            }
            for i in ranked
        ],
        "error_at_target": round(float(error[target]), 5),
        "target_weights_before": round_all(weights_before.tolist()),
        "target_weights_after": round_all(weights_after.tolist()),
        "loss": round(loss, 4),
        "target_p_before": round(float(probabilities_before[target]), 5),
        "target_p_after": round(float(probabilities_after[target]), 5),
    }

    # --- block 3: the loop, and what it makes along the way ------------------
    model = TokenLanguageModel(config, vocabulary)
    losses, samples = [], {}
    for epoch in range(EPOCHS + 1):
        if epoch in CHECKPOINTS:
            samples[str(epoch)] = [
                model.generate(temperature=0.7, random_seed=config.seed + n)
                for n in range(4)
            ]
        if epoch == EPOCHS:
            break
        losses.extend(
            model.train(
                contexts, targets, epochs=1, learning_rate=LEARNING_RATE
            )
        )

    loop_trace = {
        "epochs": EPOCHS,
        "learning_rate": LEARNING_RATE,
        "losses": round_all(losses, 4),
        "checkpoints": list(CHECKPOINTS),
        "samples": samples,
        "parameter_count": model.parameter_count,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "source": "tools/export_deck_traces.py",
                "corpus": CORPUS.name,
                "config": {
                    "context": config.context,
                    "embedding": config.embedding,
                    "seed": config.seed,
                },
                "vocabulary": vocabulary_trace,
                "step": step_trace,
                "loop": loop_trace,
            },
            indent=1,
        )
        + "\n",
        encoding="ascii",
    )
    print(
        f"{len(vocabulary)} tokens, {len(targets)} examples, "
        f"loss {losses[0]:.3f} -> {losses[-1]:.3f}, "
        f"{model.parameter_count} parameters -> {OUT.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
