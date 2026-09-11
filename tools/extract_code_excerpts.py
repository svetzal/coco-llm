#!/usr/bin/env python3
"""Pull the deck's assembly excerpts out of the real source.

`learning-journey.md` sets the rule this implements: the 6809 source is
evidence, not decoration, so an excerpt on a slide has to be the code that
actually runs. Retyping it into a slide means the slide can go stale silently
the next time the assembly changes. This reads the routines out of the source
files by label, so it cannot.

Each excerpt names a file, a starting label, and where to stop. Lines are taken
verbatim. Comments in the source are dropped, because a slide has its own
annotation and the two would compete, and dropping them is marked with the
ellipsis the discipline requires. Nothing is reordered or reworded.

`highlight` names the lines to light up, matched by their exact source text, so
a highlight cannot drift onto the wrong instruction either. A highlight that
matches nothing is an error rather than a silently missing emphasis.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
SRC = ROOT / "src" / "6809"
OUT = ROOT / "presentation" / "deck" / "data" / "code.json"

# `learning-journey.md` asks for roughly five to twelve executable lines per
# reveal. That is a real constraint on a projector, so it is enforced below
# rather than trusted.
MIN_LINES, MAX_LINES = 5, 12

EXCERPTS = {
    # The optimisation that made a live training run practical. EXP-001
    # rejected the character model on multiply cost; this is what replaced the
    # bit-at-a-time signed routine and cut the run from 38.6M instructions to
    # 15.8M without changing a single result.
    "two_muls": {
        "file": "model_forward.asm",
        "label": "multiply_s8_s16",
        "until": "tst     multiply_factor",
        "title": "one signed multiply, from two unsigned ones",
        "highlight": ["mul"],
    },
    # The second beat of the same routine: MUL is unsigned, so a negative
    # factor comes out 256 too large and one subtraction fixes it.
    "sign_fix": {
        "file": "model_forward.asm",
        "label": "multiply_s8_s16",
        "start_at": "tst     multiply_factor",
        "until": "multiply_ready",
        "title": "the correction for a negative factor",
        "highlight": ["suba"],
    },
    # Where the learning rate physically is. The deck says 1/16 on the nudge
    # slide; this is the 1/16.
    "learning_rate": {
        "file": "training.asm",
        "label": "update_weight",
        "start_at": "lbsr    experiment_multiply_training_context",
        "until": "ldx     weight_pointer",
        "title": "the learning rate, in eight instructions",
        "highlight": ["asra", "rorb"],
    },
}


def excerpt(spec: dict) -> dict:
    path = SRC / spec["file"]
    lines = path.read_text().splitlines()
    try:
        start = next(
            i for i, line in enumerate(lines) if line.rstrip() == spec["label"]
        )
    except StopIteration:
        raise SystemExit(f"{spec['file']}: no label {spec['label']!r}")

    # An excerpt may begin part-way into a routine when the earlier lines are
    # only address arithmetic. It is still labelled with the routine it came
    # from, and the omission is marked on the slide.
    begins_inside = "start_at" in spec
    taking = not begins_inside

    body, dropped = [], False
    for line in lines[start:]:
        stripped = line.strip()
        if not taking:
            if stripped == spec["start_at"]:
                taking = True
            else:
                continue
        if body and (stripped == spec["until"] or line.rstrip() == spec["until"]):
            break
        if stripped.startswith(";") or not stripped:
            dropped = True
            continue
        body.append(line.rstrip())
    if not taking:
        raise SystemExit(
            f"{spec['file']}: {spec['start_at']!r} not found in "
            f"{spec['label']!r}; the code moved"
        )
    if not MIN_LINES <= len(body) <= MAX_LINES:
        raise SystemExit(
            f"{spec['file']}: {spec['label']!r} gives {len(body)} lines; the "
            f"reveal discipline asks for {MIN_LINES} to {MAX_LINES}. Split it "
            "or narrow the range rather than putting a wall of code on a slide."
        )

    hits = sum(1 for line in body if any(h in line.split() for h in spec["highlight"]))
    if not hits:
        raise SystemExit(
            f"{spec['file']}: highlight {spec['highlight']} matches nothing in "
            f"{spec['label']!r}; the code moved and the slide would have lied"
        )

    return {
        "source": f"src/6809/{spec['file']} - {spec['label']}",
        "begins_inside": begins_inside,
        "title": spec["title"],
        "lines": [
            {
                "text": line,
                "hot": any(h in line.split() for h in spec["highlight"]),
            }
            for line in body
        ],
        "dropped_comments": dropped,
        "highlighted": hits,
    }


def main() -> None:
    built = {name: excerpt(spec) for name, spec in EXCERPTS.items()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(built, indent=1) + "\n", encoding="ascii")
    for name, data in built.items():
        print(
            f"{name}: {len(data['lines'])} lines, "
            f"{data['highlighted']} highlighted, from {data['source']}"
        )


if __name__ == "__main__":
    main()
