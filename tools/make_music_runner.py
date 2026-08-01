#!/usr/bin/env python3
"""Flatten the DECB music player into source the direct simulator can run.

The direct simulator's assembler has no `include` directive, so the player is
assembled with lwasm first and its bytes are emitted here as a literal block,
preceded by a small runner. This mirrors how the model experiments build their
simulator images.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

RUNNER_ORG = 0x1000


def symbol_address(symbols: str, name: str) -> int:
    match = re.search(
        rf"^{re.escape(name)} EQU \$([0-9A-Fa-f]+)$", symbols, re.MULTILINE
    )
    if match is None:
        raise ValueError(f"symbol not found: {name}")
    return int(match.group(1), 16)


def decb_segments(payload: bytes) -> list[tuple[int, bytes]]:
    """Split a DECB binary into (load address, data) segments."""
    segments: list[tuple[int, bytes]] = []
    offset = 0
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


def emit_block(address: int, data: bytes) -> list[str]:
    lines = [f"        org     ${address:04X}"]
    for start in range(0, len(data), 16):
        chunk = data[start : start + 16]
        lines.append("        fcb     " + ",".join(f"${byte:02X}" for byte in chunk))
    return lines


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--symbols", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    payload = arguments.binary.read_bytes()
    symbols = arguments.symbols.read_text()
    entry = symbol_address(symbols, "music_start")
    segments = decb_segments(payload)

    lines = [
        "; Generated direct-simulator image. Do not edit.",
        "; Plays the whole tune so --perf reports total cycles.",
        f"        org     ${RUNNER_ORG:04X}",
        f"start   lds     #${RUNNER_ORG - 1:04X}",
        f"        jsr     ${entry:04X}    ; music_start",
        "        clra",
        "        sta     runner_done",
        "        swi",
        "runner_done rmb 1",
        "",
    ]
    total = 0
    for address, data in segments:
        lines += emit_block(address, data)
        total += len(data)
    lines += ["", ";! runner_done = #$00", ""]

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text("\n".join(lines), encoding="ascii")
    print(f"entry: ${entry:04X}   segments: {len(segments)}   bytes: {total}")
    print(f"wrote {arguments.output}")


if __name__ == "__main__":
    main()
