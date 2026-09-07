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
PAD, HOLD, REST = 34, 32, 33
PROGRESSION = (0, 0, 3, 4)
# An octave above the tonic, matching melody_demo.asm.
SEED_FIGURE = [
    12,
    HOLD,
    14,
    HOLD,
    16,
    HOLD,
    19,
    HOLD,
    17,
    HOLD,
    14,
    HOLD,
    19,
    HOLD,
    12,
    HOLD,
]
RNG_SEED = 0x1A2B
CALLER_DP = 0xA5
# The figure entered at the keyboard: scale degrees 1-7, plus the hold and
# rest tokens the '-' and '.' keys add. Every entry lasts two rows.
TOK_HOLD, TOK_REST = 8, 9
ENTERED = (1, 3, TOK_HOLD, 5, TOK_REST, 7, 5, 1)
MAJOR_STEPS = (0, 2, 4, 5, 7, 9, 11)
SEED_OCTAVE = 12


def entry_tokens(entry: int) -> list[int]:
    """The two melody tokens one entered symbol becomes."""
    if entry == TOK_HOLD:
        return [HOLD, HOLD]  # carries the previous note through
    if entry == TOK_REST:
        return [REST, HOLD]  # silence, held
    return [MAJOR_STEPS[entry - 1] + SEED_OCTAVE, HOLD]


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
        for name in (
            "demo_compose",
            "demo_tokens",
            "demo_arrange",
            "tune_rows",
            "demo_mode",
            "demo_seed_rows",
            "mel_rng",
            "ui_last",
            "ui_panel",
            "ui_build_seed",
            "ui_seed",
            "ui_seed_len",
            "ui_mode",
            "demo_seed",
            "demo_steps",
            "event_buffer",
            "finished",
            "music_start",
        )
    }

    lines = [
        "; Generated demo parity image. Do not edit.",
        f"; {rows} rows composed, {CHECKS} sampled for comparison",
        f"        org     ${RUNNER_ORG:04X}",
        f"start   lds     #${RUNNER_ORG - 1:04X}",
        f"        jsr     ${address['ui_panel']:04X}",
        "        ldd     $0400",
        "        std     title_first",
        "        clra",
        f"        sta     ${address['demo_mode']:04X}",
        f"        sta     ${address['ui_last']:04X}",
        f"        lda     #{SEED_ROWS}",
        f"        sta     ${address['demo_seed_rows']:04X}",
        f"        ldd     #${RNG_SEED:04X}",
        f"        std     ${address['mel_rng']:04X}",
        f"        jsr     ${address['demo_compose']:04X}",
        f"        jsr     ${address['demo_arrange']:04X}",
    ]

    expectations = []
    expectations.append(";! title_first = #$190F")  # dark "YO" from "YOU SEED"
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

    # The row hook check that used to sit here is gone with the hook: the
    # steady player (EXP-018) has nothing between samples to hook.

    # The entered figure must actually reach the composer. It did not:
    # ui_step_of reloaded X, which ui_build_seed was using as its write
    # pointer, so every entered note landed in the scale tables and
    # demo_seed kept its built-in figure. Nothing had ever driven this path.
    lines.append("; --- entered seed ---")
    for index, degree in enumerate(ENTERED):
        lines.append(f"        lda     #{degree}")
        lines.append(f"        sta     ${address['ui_seed'] + index:04X}")
    lines.append(f"        lda     #{len(ENTERED)}")
    lines.append(f"        sta     ${address['ui_seed_len']:04X}")
    lines.append("        clra")
    lines.append(f"        sta     ${address['ui_mode']:04X}   ; major")
    lines.append(f"        jsr     ${address['ui_build_seed']:04X}")

    expected_seed = []
    for entry in ENTERED:
        expected_seed += entry_tokens(entry)
    for index, value in enumerate(expected_seed):
        lines.append(f"        lda     ${address['demo_seed'] + index:04X}")
        lines.append(f"        sta     sd{index}")
        expectations.append(f";! sd{index} = #${value:02X}")
    lines.append(f"        lda     ${address['demo_seed_rows']:04X}")
    lines.append("        sta     seed_rows")
    expectations.append(f";! seed_rows = #${len(expected_seed):02X}")
    # The scale tables are what the stray writes were landing in.
    for index, value in enumerate(MAJOR_STEPS):
        lines.append(f"        lda     ${address['demo_steps'] + index:04X}")
        lines.append(f"        sta     st{index}")
        expectations.append(f";! st{index} = #${value:02X}")

    # The player must hand the caller back its own direct page. It did not:
    # music_start saved DP with a direct-page store executed while DP was
    # still the caller's, so the value went to the wrong page and the restore
    # read RAM nobody had written. The UI then polled the keyboard through a
    # garbage DP and BASIC scribbled through the screen.
    # The stream is one event per pass, so the run is short: a wait of one
    # sample, then the event that sets finished.
    lines.append(f"        lda     #${CALLER_DP:02X}")
    lines.append("        tfr     a,dp")
    lines.append(f"        ldx     #${address['event_buffer']:04X}")
    lines.append("        lda     #1")
    lines.append("        sta     ,x+")
    lines.append(f"        ldd     #${address['finished']:04X}")
    lines.append("        std     ,x++")
    lines.append("        lda     #1")
    lines.append("        sta     ,x+")
    lines.append("        clr     ,x")
    lines.append(f"        jsr     ${address['music_start']:04X}")
    lines.append("        tfr     dp,a")
    lines.append("        clrb")
    lines.append("        tfr     b,dp")
    lines.append("        sta     dp_kept")
    expectations.append(f";! dp_kept = #${CALLER_DP:02X}")

    lines.append("        swi")
    for index in range(CHECKS):
        lines.append(f"t{index} rmb 1")
    lines.append("first_note rmb 1")
    lines.append("dp_kept rmb 1")
    lines.append("title_first rmb 2")
    lines.append("seed_rows rmb 1")
    for index in range(2 * len(ENTERED)):
        lines.append(f"sd{index} rmb 1")
    for index in range(len(MAJOR_STEPS)):
        lines.append(f"st{index} rmb 1")
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
