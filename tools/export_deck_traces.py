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
  draw        block 3. How the trained model picks each token: the byte it
              draws, the stretch of 0..255 every token owns, and which one
              the byte landed on, for the first two seeds the CoCo shows.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from fixed_token_lm import FixedTokenLanguageModel, XorShift16
from token_lm import (
    BOUNDARY,
    ModelConfig,
    TokenLanguageModel,
    assess_samples,
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
        "focus_tokens": [{"text": t, "id": token_by_text[t]} for t in focus_tokens],
        "boundary": boundary,
        "walk": walk,
        "names": len(names),
        "examples": len(targets),
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
                "repeats": sum(
                    1 for text in drawn if len(set(text.split())) < len(text.split())
                ),
                "both": sum(1 for a in assessed if a.novel and a.name_like),
            }
            samples[str(epoch)] = [
                {
                    "text": (text := drawn[n]),
                    "novel": text not in corpus,
                    # Saying the same token twice is a different failure from
                    # saying something untrue, and it disappears earlier. It
                    # is the step from "starts like a name" to "hangs
                    # together".
                    "repeats": len(set(text.split())) < len(text.split()),
                }
                for n in range(4)
            ]
        if epoch == EPOCHS:
            break
        losses.extend(
            model.train(contexts, targets, epochs=1, learning_rate=LEARNING_RATE)
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
        "examples": len(targets),
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
        "examples": len(targets),
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

    # --- what the four shifts actually do ------------------------------------
    # The learning-rate code slide shows eight instructions. This is the value
    # they operate on, so the code slide and the One Step slide can be shown to
    # be the same arithmetic rather than merely described as related.
    #
    # The 6809 holds the gradient in D, which is the A and B registers side by
    # side. ASRA shifts A right and drops its low bit into the carry; RORB
    # rotates that carry into the top of B. The pair is one arithmetic shift of
    # the whole 16-bit value, and four pairs divide it by sixteen.
    #
    # Q4.12 means twelve fractional bits, so the integer is the real value
    # times 4096.
    Q = 4096
    output_error = float(probabilities_before[target]) - 1.0
    gradient = output_error * vector_display[0]
    steps = [{"value": round(gradient * Q), "dropped": None}]
    for _ in range(4):
        previous = steps[-1]["value"]
        steps.append({"value": previous >> 1, "dropped": previous & 1})
    assert round(steps[-1]["value"] / Q, 4) == abs(nudges[0]["change"]), (
        "the shift must land on the change the One Step slide shows; if it "
        "does not, one of the two figures is lying"
    )

    shift = {
        "fraction_bits": 12,
        "scale": Q,
        "label": f"error x context for {vocabulary[target]}'s first weight",
        "steps": [
            {
                "value": step["value"],
                "bits": format(step["value"], "016b"),
                "real": round(step["value"] / Q, 4),
                "dropped": step["dropped"],
            }
            for step in steps
        ],
    }

    # --- why the sign correction is one subtraction --------------------------
    # MUL is unsigned. A negative 8-bit factor arrives as its two's complement,
    # which is 256 too large, so the product is too large by 256 x multiplier.
    # In the low sixteen bits that excess is exactly the multiplier's low byte
    # sitting in the high half, which is why one SUBA fixes it.
    #
    # A worked instance rather than a captured one: these are not the operands
    # of a specific training step, they are a factor and a multiplier chosen to
    # sit inside EXP-004's measured product range so the result is honest about
    # what the routine actually handles.
    SIGN_FACTOR, SIGN_MULTIPLIER = -121, 60
    unsigned_factor = SIGN_FACTOR & 0xFF
    raw_product = (unsigned_factor * SIGN_MULTIPLIER) & 0xFFFF
    excess_high = SIGN_MULTIPLIER & 0xFF
    corrected = (raw_product - excess_high * 256) & 0xFFFF
    as_signed = corrected - 0x10000 if corrected >= 0x8000 else corrected
    assert as_signed == SIGN_FACTOR * SIGN_MULTIPLIER, "the correction must be exact"
    assert abs(as_signed) <= 11_408, (
        "outside EXP-004's measured product range, so the low word would not "
        "be the whole answer and the slide would be misleading"
    )

    sign_fix = {
        "factor": SIGN_FACTOR,
        "unsigned_factor": unsigned_factor,
        "multiplier": SIGN_MULTIPLIER,
        "raw": raw_product,
        "excess_high": excess_high,
        "corrected": corrected,
        "signed": as_signed,
        "measured_max": 11_408,
    }

    # --- how the next token is picked ----------------------------------------
    # The CoCo does not take the best token. It draws one byte from xorshift16
    # and walks the vocabulary adding up shares of 256 until the running total
    # passes the byte. That is a number line from 0 to 255 cut into 29
    # stretches, and the figure draws exactly that, from the integer model the
    # CoCo runs, so the bytes and the stretches are the ones behind the first
    # names on its screen. The walk is checked against the model's own
    # generate() so the figure cannot describe a different procedure.
    fixed = FixedTokenLanguageModel(config, vocabulary)
    fixed.train(contexts, targets, epochs=CHOSEN_EPOCHS)
    boundary = token_by_text[BOUNDARY]
    MINIMUM_TOKENS = 2

    def walk(seed: int) -> dict:
        random = XorShift16(seed)
        context = [boundary] * config.context
        produced: list[str] = []
        steps = []
        for _ in range(6):
            _, shares = fixed._forward(np.asarray(context, dtype=np.int64))
            shares = shares.copy()
            # For the first two tokens END's stretch is handed to the
            # favourite, so a name is never one word. A rule in the code,
            # not in the weights, and the slide says so.
            floored = len(produced) < MINIMUM_TOKENS
            if floored:
                moved = int(shares[boundary])
                shares[boundary] = 0
                shares[int(np.argmax(shares))] += moved
            assert int(np.sum(shares)) == 256
            draw = random.next() & 0xFF
            stretches, running, chosen = [], 0, None
            for token, share in enumerate(shares):
                share = int(share)
                if share:
                    stretches.append(
                        {
                            "text": vocabulary[token],
                            "share": share,
                            "start": running,
                            "end": running + share,
                            "hit": chosen is None and draw < running + share,
                        }
                    )
                    if stretches[-1]["hit"]:
                        chosen = token
                running += share
            favourite = int(np.argmax(shares))
            steps.append(
                {
                    "draw": draw,
                    "chosen": vocabulary[chosen],
                    "share": int(shares[chosen]),
                    "favourite": vocabulary[favourite],
                    "favourite_share": int(shares[favourite]),
                    "floored": floored,
                    "stretches": stretches,
                }
            )
            if chosen == boundary:
                break
            produced.append(vocabulary[chosen])
            context = context[1:] + [chosen]
        text = " ".join(produced)
        assert text == fixed.generate(random_seed=seed), (
            "the walk must reproduce generate(); otherwise the slide describes "
            "a procedure the machine does not run"
        )
        return {"seed": seed, "text": text, "steps": steps}

    draw_trace = {
        "epochs": CHOSEN_EPOCHS,
        "minimum_tokens": MINIMUM_TOKENS,
        "total": 256,
        "walks": [walk(config.seed), walk(config.seed + 1)],
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
                "draw": draw_trace,
                "why_three": why_three,
                "parameters": parameters,
                "budget": budget,
                "shift": shift,
                "sign_fix": sign_fix,
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
