#!/usr/bin/env python3
"""Prove the CoCo writes the same screen of titles the Mac predicts.

The generator is a long chain - a masked forward pass per frame token, two
constrained noun draws, a render, a fingerprint check, and a retry loop around
all of it - sharing one XorShift16 stream. Any disagreement anywhere shows up
as a different screen, so the screen is what gets compared.

Row zero is checked cell by cell, because a failure there is readable. The
other fifteen are covered by a checksum the runner computes over the whole
screen, which costs 1 criterion instead of 480 and still catches a single
wrong character.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))
sys.path.insert(0, str(ROOT / "tools"))

from fixed_token_lm import XorShift16
from run_exp_012 import build, generate
from run_exp_012 import parse_arguments as reference_arguments
from title_generator import title_hash

BINARY = ROOT / "build" / "coco-titles.bin"
SYMBOLS = ROOT / "build" / "coco-titles.sym"
RUNNER_ORG = 0x0C00
SCREEN = 0x0400
ROWS, COLUMNS = 16, 32
BLANK = 0x60
RNG_SEED = 0x1A2B


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


def expected_screen() -> tuple[list[int], list[str]]:
    """The 512 VDG cells the CoCo should end up with, and the titles in them."""
    sys.argv = [sys.argv[0]]
    model, filler, allowed, _, titles, _ = build(reference_arguments())
    random = XorShift16(RNG_SEED)
    forbidden = {title_hash(title) for title in titles}

    cells = [BLANK] * (ROWS * COLUMNS)
    produced: list[str] = []
    for row in range(ROWS):
        title = generate(model, filler, allowed, random, forbidden)
        produced.append(title or "")
        if title is None:
            continue
        forbidden.add(title_hash(title))
        for column, character in enumerate(title):
            # Normal video, black on green: uppercase ASCII $40-$5F is
            # already the VDG code; space and punctuation shift up by $40.
            # The old & 0x3F produced the inverse-video range.
            value = ord(character)
            cells[row * COLUMNS + column] = value if value >= 0x40 else value + 0x40
    return cells, produced


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()

    symbols = SYMBOLS.read_text()
    address = {
        name: symbol(symbols, name)
        for name in (
            "load_parameters",
            "fill_screen",
            "level_name",
            "reset_level_names",
            "rng_state",
        )
    }
    cells, titles = expected_screen()

    checksum = 0
    for value in cells:
        checksum = ((checksum << 1 | checksum >> 15) + value) & 0xFFFF

    lines = [
        "; Generated EXP-012 title parity image. Do not edit.",
        f"; {sum(1 for t in titles if t)} of {ROWS} rows filled",
        *(f";   {title}" for title in titles if title),
        f"        org     ${RUNNER_ORG:04X}",
        f"start   lds     #${RUNNER_ORG - 1:04X}",
        f"        jsr     ${address['load_parameters']:04X}",
        f"        ldd     #${RNG_SEED:04X}",
        f"        std     ${address['rng_state']:04X}",
        f"        jsr     ${address['fill_screen']:04X}",
        "; --- row zero, cell by cell ---",
    ]
    expectations = []
    for column in range(COLUMNS):
        lines.append(f"        lda     ${SCREEN + column:04X}")
        lines.append(f"        sta     c{column:02d}")
        expectations.append(f";! c{column:02d} = #${cells[column]:02X}")

    # Rotate-and-add over all 512 cells: cheap, order-sensitive, and it moves
    # if any single character does.
    lines += [
        "; --- checksum over the whole screen ---",
        "        clra",
        "        clrb",
        "        std     sum",
        f"        ldx     #${SCREEN:04X}",
        "sum_next",
        "        ldd     sum",
        "        aslb",
        "        rola",
        "        adcb    #0",
        "        std     sum",
        "        clra",
        "        ldb     ,x+",
        "        addd    sum",
        "        std     sum",
        f"        cmpx    #${SCREEN + ROWS * COLUMNS:04X}",
        "        blo     sum_next",
    ]
    expectations.append(f";! sum = #${checksum:04X}")

    # The game shows one name on the top row, centred. Same generator, same
    # stream, so the first level name is the first title of the screen above.
    # A title bar is drawn from the reversed set, whose blank is $20 - not
    # the $60 the body uses. screen_title_bar owns that now.
    first = titles[0]
    indent = (COLUMNS - len(first)) // 2
    centred = [0x20] * COLUMNS
    for offset, character in enumerate(first):
        centred[indent + offset] = ord(character) & 0x3F
    lines += [
        "; --- one centred level name ---",
        f"        jsr     ${address['reset_level_names']:04X}",
        f"        ldd     #${RNG_SEED:04X}",
        f"        std     ${address['rng_state']:04X}",
        f"        jsr     ${address['level_name']:04X}",
    ]
    for column in range(COLUMNS):
        lines.append(f"        lda     ${SCREEN + column:04X}")
        lines.append(f"        sta     L{column:02d}")
        expectations.append(f";! L{column:02d} = #${centred[column]:02X}")
    # Every reservation sits past the final swi. Left among the code, they are
    # executed: a block of rmb between two phases ran as instructions.
    lines.append("        swi")
    lines.append("sum     rmb     2")
    lines += [f"c{column:02d} rmb 1" for column in range(COLUMNS)]
    lines += [f"L{column:02d} rmb 1" for column in range(COLUMNS)]
    lines.append("")

    for load, data in decb_segments(BINARY.read_bytes()):
        lines.append(f"        org     ${load:04X}")
        for start in range(0, len(data), 16):
            chunk = data[start : start + 16]
            lines.append("        fcb     " + ",".join(f"${b:02X}" for b in chunk))

    lines += ["", *expectations, ""]
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text("\n".join(lines), encoding="ascii")

    print(f"{sum(1 for t in titles if t)}/{ROWS} rows, checksum ${checksum:04X}")
    print(f"first row: {titles[0]!r}")
    print(f"wrote {arguments.output}")


if __name__ == "__main__":
    main()
