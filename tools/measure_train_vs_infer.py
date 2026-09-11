#!/usr/bin/env python3
"""Split the assembled image into what learns and what uses what was learned.

The deck claims the CoCo both trains a model and runs it. Those are different
jobs and they do not cost the same, so this measures which bytes belong to
which. The split is the same one the source already makes: model_forward.asm
was extracted from model_core.asm precisely so a Mac-trained experiment could
run inference without assembling the training driver.

Every byte is attributed by symbol, and a symbol's size is the distance to the
next one. The classification is a judgement about each routine's job, so it
lives here in one table rather than being inferred, and anything unclassified
fails loudly instead of quietly landing in a bucket.
"""

from __future__ import annotations

import collections
import itertools
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).parents[1]
SRC = ROOT / "src" / "6809"
SYMBOLS = ROOT / "build" / "coco-llm.sym"
DATA_INC = ROOT / "build" / "model_data.inc"
OUT = ROOT / "presentation" / "deck" / "data" / "traces.json"
IMAGE_START, IMAGE_END = 0x2000, 0x2D1B

CHAIN = [
    "experiments/experiment_004.asm",
    "experiments/sample_gallery.asm",
    "model_core.asm",
    "model_forward.asm",
    "training.asm",
    "inference.asm",
    "screen.asm",
    "model_storage.asm",
]

# Whole modules whose job is unambiguous.
BY_FILE = {
    "training.asm": "learn",  # epoch and example loops, gradient updates
    "model_forward.asm": "both",  # forward pass, softmax, fixed-point multiply
    "inference.asm": "use",  # the next-token loop
    "sample_gallery.asm": "use",  # showing what it generated
    "experiment_004.asm": "both",  # the driver: calls training, then inference
}

# Routines inside mixed modules, named individually.
BY_SYMBOL = {
    # model_core.asm: setting up and checking the training run.
    "initialize_model": "learn",
    "initialize_random_parameter": "learn",
    "clear_bias": "learn",
    "verify_parameters": "verify",
    "verify_parameter": "verify",
    "verify_failed": "verify",
    "verification_failed": "verify",
    "verification_halt": "verify",
    "finish_training": "learn",
    "wait_for_key": "both",
    # screen.asm: the training progress display.
    "initialize_training_screen": "learn",
    "clear_training_rows": "learn",
    "display_training_example": "learn",
    "clear_training_example": "learn",
    "show_training_complete": "learn",
    "message_complete": "learn",
    "message_press_key": "learn",
    "write_decimal_2": "learn",
    "decimal_tens": "learn",
    "decimal_ready": "learn",
    "show_verification_failed": "verify",
    "message_verification_failed": "verify",
    # screen.asm: showing generated tokens.
    "print_token_id": "use",
    "print_token_id_text": "use",
    "print_token_id_ready": "use",
    "print_token_id_dark": "use",
    "print_token_id_dark_text": "use",
    "message_generating": "use",
    "message_generated": "use",
    "message_seed": "use",
    # screen.asm: three short strings. message_arrow and message_space appear
    # only in the training-example display; message_boundary is the "#" that
    # stands in for <END>, and inference.asm prints it too.
    "message_arrow": "learn",
    "message_space": "learn",
    "message_boundary": "both",
    # screen.asm: plain drawing, used by both phases.
    "clear_screen": "both",
    "fill_title_bar": "both",
    "print_string": "both",
    "print_string_done": "both",
    "print_black_on_green": "both",
    "print_black_on_green_done": "both",
    # The generated data fixture.
    "training_examples": "learn",  # the corpus, only needed while learning
    "exp_lut": "both",  # softmax lookup, both phases
    "token_pointers": "use",  # token spellings, only needed to print
    "expected_parameters": "verify",
    "expected_checksum_text": "verify",
}


def owners() -> dict[str, str]:
    found: dict[str, str] = {}
    for relative in CHAIN:
        for line in (SRC / relative).read_text().splitlines():
            match = re.match(r"^([A-Za-z_]\w*)", line)
            if match:
                found.setdefault(match.group(1), relative.split("/")[-1])
    for line in DATA_INC.read_text().splitlines():
        match = re.match(r"^([A-Za-z_]\w*)", line)
        if match:
            found.setdefault(match.group(1), "model_data.inc")
    return found


def main() -> None:
    owner = owners()
    symbols = sorted(
        (int(m.group(2), 16), m.group(1))
        for m in re.finditer(
            r"^(\w+) EQU \$([0-9A-Fa-f]+)$", SYMBOLS.read_text(), re.MULTILINE
        )
    )

    buckets: collections.Counter[str] = collections.Counter()
    unclassified = []
    for (address, name), (following, _) in itertools.pairwise(symbols):
        if not IMAGE_START <= address < IMAGE_END:
            continue
        size = min(following, IMAGE_END) - address
        if not size:
            continue
        job = BY_SYMBOL.get(name) or BY_FILE.get(owner.get(name, ""))
        # Token spelling labels are generated one per token; match by shape.
        if job is None and re.match(r"^token_\d\d_", name):
            job = "use"
        if job is None:
            unclassified.append((name, owner.get(name, "??"), size))
            continue
        buckets[job] += size

    if unclassified:
        for name, where, size in unclassified:
            print(f"  unclassified: {name} ({where}) {size} bytes")
        raise SystemExit(
            f"{len(unclassified)} symbols have no job; classify them in "
            "BY_SYMBOL or BY_FILE rather than letting them land anywhere"
        )

    traces = json.loads(OUT.read_text())
    budget = traces["budget"]
    weights = budget["bytes"]
    split = {
        "learn_only": buckets["learn"],
        "use_only": buckets["use"],
        "shared": buckets["both"],
        "verify": buckets["verify"],
        "weights": weights,
        # What a machine needs to run the finished model, and what it needs on
        # top of that to have produced it in the first place.
        "to_use": buckets["use"] + buckets["both"] + weights,
        "to_learn": buckets["learn"],
    }
    traces["split"] = split

    # The budget's own memory figures are restated from this classification,
    # because it is the more accurate one: the earlier split counted the 92
    # bytes of verification CODE as ordinary program, when it belongs with the
    # fixture it checks against.
    budget["verify_bytes"] = split["verify"]
    budget["running_bytes"] = (
        split["to_use"] + split["to_learn"] + budget["working_bytes"]
    )
    budget["total_bytes"] = budget["running_bytes"] + split["verify"]
    budget["fixture_bytes"] = split["verify"]

    OUT.write_text(json.dumps(traces, indent=1) + "\n", encoding="ascii")

    total = sum(buckets.values())
    for job in ("learn", "use", "both", "verify"):
        print(f"{buckets[job]:>6}  {job}")
    print(f"{total:>6}  image (checks against {IMAGE_END - IMAGE_START})")
    print()
    print(f"{split['to_use']:>6}  to RUN the trained model (use + shared + weights)")
    print(f"{split['to_learn']:>6}  more, to TRAIN it")
    print(f"{budget['running_bytes']:>6}  both, with working space")
    print(f"{budget['total_bytes']:>6}  as built, with the self-check")


if __name__ == "__main__":
    main()
