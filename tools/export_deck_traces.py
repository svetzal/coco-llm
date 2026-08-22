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
    assess_samples,
    TokenLanguageModel,
    build_vocabulary,
    load_names,
    make_examples,
)

CORPUS = ROOT / "experiments" / "data" / "EXP-002-tokenized-computer-names.txt"
OUT = ROOT / "presentation" / "deck" / "data" / "traces.json"

# The name the whole talk keeps returning to.
FOCUS = "COMMODORE AMIGA"
# 1/16, because that is what the 6809 does: update_weight in training.asm
# shifts the gradient right four times. EXP-002 records the same choice, made
# so the rate is a shift rather than a multiply. The deck must use the
# machine's number, not a nicer-looking one.
LEARNING_RATE = 1 / 16
EPOCHS = 60
CHECKPOINTS = (0, 1, 5, 20, EPOCHS)
# The number the project actually ships, from EXP-002 and EXP-004. The run
# above goes past it on purpose: 60 epochs is evidence that 20 was enough, not
# a competing choice. Every cost figure uses 20.
CHOSEN_EPOCHS = 20
NOVELTY_SAMPLES = 200
SYMBOLS = ROOT / "build" / "coco-llm.sym"


def symbol(name: str) -> int:
    """Read an address out of the assembler's symbol dump."""
    import re

    match = re.search(
        rf"^{re.escape(name)} EQU \$([0-9A-Fa-f]+)$", SYMBOLS.read_text(), re.MULTILINE
    )
    if match is None:
        raise SystemExit(f"symbol not found in {SYMBOLS.name}: {name}")
    return int(match.group(1), 16)


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

    # The whole lookup table, both slots. 2 slots x 29 words x 3 numbers is
    # 174 of the model's 290 parameters, so this IS most of the model, and a
    # figure that shows a row being fetched should be able to show what it was
    # fetched from.
    tables = [
        {
            "slot": position + 1,
            "rows": [
                {
                    "text": vocabulary[token],
                    "row": round_all(
                        model.position_embeddings[position, token].tolist()
                    ),
                    "used": bool(token == ctx[position]),
                }
                for token in range(len(vocabulary))
            ],
        }
        for position in range(config.context)
    ]

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

    # --- the nudge, number by number -----------------------------------------
    # The correction to the right answer's row is one multiplication repeated
    # three times:
    #
    #     change = learning rate x how wrong we were x the incoming number
    #
    # so the SIGN of each change is the sign of the corresponding context
    # number. Where the context went negative the weight goes down. That is
    # the whole of backpropagation at this scale and it is worth showing
    # rather than asserting.
    #
    # The changes are computed from the DISPLAYED before and after values, so
    # the column adds up on screen. The factor is exported alongside for the
    # formula line; multiplying it out agrees to within the last digit.
    wrongness = 1.0 - float(probabilities_before[target])
    factor = LEARNING_RATE * wrongness
    nudges = []
    for i in range(config.embedding):
        was = round(float(weights_before[i]), 4)
        now = round(float(weights_after[i]), 4)
        nudges.append(
            {
                # The value shown on the lookup slide, so both agree.
                "incoming": vector_display[i],
                "before": was,
                "change": round(now - was, 4),
                "after": now,
                "up": now > was,
            }
        )

    step_trace = {
        "nudges": nudges,
        "wrongness": round(wrongness, 4),
        "factor": round(factor, 4),
        "context_text": example["context_text"],
        "target_text": example["target_text"],
        "target": target,
        "learning_rate": LEARNING_RATE,
        "tables": tables,
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
    losses, samples, novelty = [], {}, {}
    for epoch in range(EPOCHS + 1):
        if epoch in CHECKPOINTS:
            # Whether a sample is novel or copied straight out of the corpus
            # is the thing that turns later in the run, so it is recorded
            # rather than judged by eye on stage.
            corpus = {name.strip() for name in names}
            # Two samples get shown; the novelty rate is measured over many
            # more, because "it started reciting" is a claim about behaviour
            # and two draws cannot support it.
            drawn = [
                model.generate(temperature=0.7, random_seed=config.seed + n)
                for n in range(NOVELTY_SAMPLES)
            ]
            # Two axes, not one. Novelty alone rewards the untrained model,
            # which invents constantly and never produces a name. name_like
            # is EXP-002's rubric, written before any sample was seen: two to
            # four tokens, first token a manufacturer that starts a real name.
            assessed = assess_samples(drawn, names)
            novelty[str(epoch)] = {
                "drawn": len(drawn),
                "copied": sum(1 for text in drawn if text in corpus),
                "name_like": sum(1 for a in assessed if a.name_like),
                "both": sum(1 for a in assessed if a.novel and a.name_like),
            }
            samples[str(epoch)] = [
                {
                    "text": (
                        text := model.generate(
                            temperature=0.7, random_seed=config.seed + n
                        )
                    ),
                    "novel": text not in corpus,
                }
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
        "chosen": CHOSEN_EPOCHS,
        "learning_rate": LEARNING_RATE,
        "losses": round_all(losses, 4),
        "checkpoints": list(CHECKPOINTS),
        "samples": samples,
        "novelty": novelty,
        "parameter_count": model.parameter_count,
    }

    # --- why three numbers ---------------------------------------------------
    # Because every extra number costs multiplies, and multiplies are what the
    # machine does not have. EXP-001 rejected the character model on exactly
    # this arithmetic: 12,859,560 multiplies is about 159 seconds of bare MUL
    # instructions at 11 cycles on a 0.89 MHz 6809, against a 180-second
    # budget, before any load, store, sign correction or softmax.
    #
    # The work is linear in the embedding width, so the table below is the
    # cost of the same run at each width. These are floors, not runtimes: MUL
    # instructions alone, nothing else counted. EXP-001 uses the same floor
    # argument, and the copy discipline allows a floor as long as it is
    # labelled one.
    MUL_CYCLES = 11
    CLOCK_HZ = 894_886
    widths = []
    for width in range(1, 7):
        per_example = 3 * len(vocabulary) * width
        total = per_example * len(targets) * 20
        widths.append(
            {
                "embedding": width,
                "per_example": per_example,
                "total": total,
                "floor_seconds": round(total * MUL_CYCLES / CLOCK_HZ, 1),
                "parameters": (
                    config.context * len(vocabulary) * width
                    + len(vocabulary) * width
                    + len(vocabulary)
                ),
                "chosen": width == config.embedding,
            }
        )

    why_three = {
        "widths": widths,
        "epochs": 20,
        "examples": int(len(targets)),
        "mul_cycles": MUL_CYCLES,
        "clock_hz": CLOCK_HZ,
        # The architecture this one replaced, for scale.
        "rejected": {
            "what": "the character model",
            "multiplies": 12_859_560,
            "floor_seconds": round(12_859_560 * MUL_CYCLES / CLOCK_HZ, 1),
        },
        "budget_seconds": 180,
    }

    # --- what a parameter is -------------------------------------------------
    # "Parameters" is the word everybody has heard about these systems and
    # almost nobody has had explained. This model has 290 and every one can be
    # accounted for, so the arithmetic is exported rather than asserted. The
    # counts are read off the model's own arrays: if the architecture changes,
    # the slide changes with it or the assertion below fails.
    positions, outputs, biases = model.parameters
    parts = [
        {
            "what": "a row for every window position and token",
            "terms": [config.context, len(vocabulary), config.embedding],
            "labels": ["context window", "tokens", "numbers"],
            "count": int(positions.size),
        },
        {
            "what": "a row for every token it can predict",
            "terms": [len(vocabulary), config.embedding],
            "labels": ["tokens", "numbers"],
            "count": int(outputs.size),
        },
        {
            "what": "one starting nudge per token",
            "terms": [len(vocabulary)],
            "labels": ["tokens"],
            "count": int(biases.size),
        },
    ]
    assert sum(p["count"] for p in parts) == model.parameter_count
    for part in parts:
        product = 1
        for term in part["terms"]:
            product *= term
        assert product == part["count"], part

    parameters = {
        "parts": parts,
        "total": model.parameter_count,
        # For scale, and because it is the number people have actually heard.
        "gpt3": 175_000_000_000,
    }

    # --- what the two choices cost -------------------------------------------
    # Epochs and parameter count are both budget decisions, and the budget has
    # two halves: time, which multiplies buy, and memory, which parameters
    # occupy. The byte figure is measured off the assembled 6809 build rather
    # than calculated here, because the parameters are Q4.12 and a wrong
    # assumption about their width would be invisible.
    # No seconds here. exhibit-copy.md forbids a runtime claim until it is
    # measured on physical hardware, and the ~75s figure for this run is a
    # cycle-model projection. Multiplies and instructions are counts, so they
    # can be shown; what they take in wall time cannot, yet.
    # "Code" was doing too much work as a label, so the image is broken down
    # by what each region actually is. Reading it off the symbol dump means
    # the figure tracks the build rather than a stale hand count.
    #
    #   $2000                6809 routines and the on-screen message strings
    #   training_examples    what the program needs to run: the 58 examples,
    #                        the 256-byte softmax lookup, the token strings
    #   expected_parameters  the self-check fixture: the reference model's
    #                        final weights and its checksum, so the CoCo can
    #                        prove it trained to the same numbers as the Mac.
    #                        Real integrity machinery, and not part of what
    #                        the model needs to exist.
    #   position_embeddings  the weights
    #   context_vector       working space
    code_start = 0x2000
    code_bytes = symbol("training_examples") - code_start
    data_bytes = symbol("expected_parameters") - symbol("training_examples")
    fixture_bytes = symbol("position_embeddings") - symbol("expected_parameters")
    parameter_bytes = symbol("parameters_end") - symbol("position_embeddings")
    working_bytes = symbol("sample_count") + 2 - symbol("context_vector")
    per_example = 3 * len(vocabulary) * config.embedding
    running = code_bytes + data_bytes + parameter_bytes + working_bytes
    budget = {
        "epochs": CHOSEN_EPOCHS,
        "examples": int(len(targets)),
        "per_example": per_example,
        "multiplies": per_example * len(targets) * CHOSEN_EPOCHS,
        # Measured by instrumenting the exact 20-epoch reference run; see
        # EXP-004's performance section.
        "instructions": 15_824_366,
        "parameters": model.parameter_count,
        "bytes_each": parameter_bytes // model.parameter_count,
        "bytes": parameter_bytes,
        "code_bytes": code_bytes,
        "data_bytes": data_bytes,
        "fixture_bytes": fixture_bytes,
        "working_bytes": working_bytes,
        "running_bytes": running,
        "total_bytes": running + fixture_bytes,
        "machine_bytes": 32 * 1024,
        # The machine the talk is about shipped in a 4K base model. Announced
        # 31 July 1980, on sale that September, catalogue 26-3001, US$399.
        "baseline_bytes": 4 * 1024,
        "launch_year": 1980,
        "target_seconds": 180,
    }
    assert budget["bytes"] == model.parameter_count * budget["bytes_each"]

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
                "why_three": why_three,
                "parameters": parameters,
                "budget": budget,
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
