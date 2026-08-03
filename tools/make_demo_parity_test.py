#!/usr/bin/env python3
"""Prove the CoCo composes the same tune the reference does.

Runs demo_compose in the direct simulator and checks the tokens it produced
against a Python replica of the same procedure: same seed figure, same chord
progression, same generator seed.

This is the end-to-end check. The inference and sampler were already proven
row by row; this proves the loop around them - the rolling history, the chord
and beat frame, the seed handover - agrees too.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from fixed_token_lm import XorShift16
from melody_fixed import draw_token

MANIFEST = ROOT / "build" / "exp010" / "melody_model.json"
BINARY = ROOT / "build" / "coco-melody-demo.bin"
SYMBOLS = ROOT / "build" / "coco-melody-demo.sym"
RUNNER_ORG = 0x0C00

BAR_ROWS = 8
SEED_ROWS = 16
MODE, METRE = 0, 3
PAD, HOLD = 34, 32
PROGRESSION = (0, 0, 3, 4)
SEED_FIGURE = [0, HOLD, 2, HOLD, 4, HOLD, 7, HOLD, 5, HOLD, 2, HOLD, 7, HOLD, 0, HOLD]
RNG_SEED = 0x1A2B
CHECKS = 12


def symbol(text: str, name: str) -> int:
    match = re.search(rf"^{re.escape(name)} EQU \$([0-9A-Fa-f]+)$", text, re.MULTILINE)
    if match is None:
        raise ValueError(f"symbol not found: {name}")
    return int(match.group(1), 16)


def decb_segments(payload: bytes) -> list[tuple[int, bytes]]:
    segments, offset = [], 0
    while offset < len(payload):
        flag = payload[offset]
        length = int.from_bytes(payload[offset + 1 : offset + 3], "big")
        address = int.from_bytes(payload[offset + 3 : offset + 5], "big")
        offset += 5
        if flag == 0xFF:
            break
        segments.append((address, payload[offset : offset + length]))
        offset += length
    return segments


def compose(manifest: dict, rows: int) -> list[int]:
    embeddings = [np.asarray(t, dtype=np.int64) for t in manifest["embeddings"]]
    weights = np.asarray(manifest["weights"], dtype=np.int64)
    biases = np.asarray(manifest["biases"], dtype=np.int64)
    history = [PAD] * manifest["history"]
    random = XorShift16(RNG_SEED)
    tokens: list[int] = []

    for row in range(rows):
        beat = row % BAR_ROWS
        chord = PROGRESSION[(row // BAR_ROWS) % len(PROGRESSION)]
        context = [MODE, METRE, chord, beat, *history]
        if row < SEED_ROWS:
            token = SEED_FIGURE[row]
        else:
            vector = sum(embeddings[p][t] for p, t in enumerate(context))
            token = draw_token(weights @ vector + biases, random)
        tokens.append(token)
        history = history[1:] + [token]

    return tokens


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    symbols = SYMBOLS.read_text()
    rows = int(
        re.search(r"^TUNE_ROWS EQU \$([0-9A-Fa-f]+)$", symbols, re.MULTILINE).group(1),
        16,
    )
    tokens = compose(manifest, rows)

    address = {
        name: symbol(symbols, name)
        for name in ("demo_compose", "demo_tokens", "demo_arrange", "tune_rows")
    }

    lines = [
        "; Generated demo parity image. Do not edit.",
        f"; {rows} rows composed, {CHECKS} sampled for comparison",
        f"        org     ${RUNNER_ORG:04X}",
        f"start   lds     #${RUNNER_ORG - 1:04X}",
        f"        jsr     ${address['demo_compose']:04X}",
        f"        jsr     ${address['demo_arrange']:04X}",
    ]

    expectations = []
    stride = max(1, rows // CHECKS)
    for index in range(CHECKS):
        row = index * stride
        lines.append(f"        lda     ${address['demo_tokens'] + row:04X}")
        lines.append(f"        sta     t{index}")
        expectations.append(f";! t{index} = #${tokens[row]:02X}")
    # The melody cell of an arranged row is the second voice: offset 3.
    lines.append(f"        lda     ${address['tune_rows'] + 3:04X}")
    lines.append("        sta     first_note")
    expectations.append(f";! first_note = #${(tokens[0] + 60) & 0xFF:02X}")

    lines.append("        swi")
    for index in range(CHECKS):
        lines.append(f"t{index} rmb 1")
    lines.append("first_note rmb 1")
    lines.append("")

    for load, data in decb_segments(BINARY.read_bytes()):
        lines.append(f"        org     ${load:04X}")
        for start in range(0, len(data), 16):
            chunk = data[start : start + 16]
            lines.append("        fcb     " + ",".join(f"${b:02X}" for b in chunk))

    lines += ["", *expectations, ""]
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text("\n".join(lines), encoding="ascii")

    distinct = len(set(tokens[SEED_ROWS:]))
    print(f"{rows} rows, {distinct} distinct tokens composed")
    print(f"first 16 composed: {tokens[SEED_ROWS : SEED_ROWS + 16]}")
    print(f"wrote {arguments.output}")


if __name__ == "__main__":
    main()
