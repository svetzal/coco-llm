"""Wrap an LWASM raw binary in source understood by the direct simulator."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def symbol_address(symbols: str, name: str) -> int:
    match = re.search(
        rf"^{re.escape(name)} EQU \$([0-9A-Fa-f]+)$", symbols, re.MULTILINE
    )
    if match is None:
        raise ValueError(f"symbol not found: {name}")
    return int(match.group(1), 16)


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
    start = symbol_address(symbols, "start")
    parity = symbol_address(symbols, "parity_result")
    mismatch_offset = symbol_address(symbols, "mismatch_offset")
    mismatch_actual = symbol_address(symbols, "mismatch_actual")
    mismatch_expected = symbol_address(symbols, "mismatch_expected")
    last_epoch_displayed = symbol_address(symbols, "last_epoch_displayed")

    lines = [
        "; Generated direct-simulator image. Do not edit.",
        f"        org     ${start:04x}",
    ]
    for offset in range(0, len(payload), 16):
        values = ",".join(f"${value:02x}" for value in payload[offset : offset + 16])
        lines.append(f"        fcb     {values}")
    lines.extend(
        [
            "",
            f"parity_result   equ     ${parity:04x}",
            f"mismatch_offset equ     ${mismatch_offset:04x}",
            f"mismatch_actual equ     ${mismatch_actual:04x}",
            f"mismatch_expect equ     ${mismatch_expected:04x}",
            f"last_epoch      equ     ${last_epoch_displayed:04x}",
            "title_first     equ     $0400",
            "complete_first  equ     $0420",
            "generated_first equ     $0460",
            "seed_1_first    equ     $0480",
            "sample_1_first  equ     $0486",
            "sample_2_first  equ     $04a6",
            "sample_3_first  equ     $04c6",
            "sample_4_first  equ     $04e6",
            "sample_5_first  equ     $0506",
            "sample_10_last  equ     $05bf",
            ";! parity_result = #$01",
            ";! mismatch_offset = #$ffff",
            ";! mismatch_actual = #$00",
            ";! mismatch_expect = #$00",
            ";! last_epoch = #20",
            "; TRAINING COMPLETE, GENERATION COMPLETE.",
            ";! title_first = #$030f",
            ";! complete_first = #$5452",
            ";! generated_first = #$4745",
            ";! seed_1_first = #$6360",
            "; COMMODORE, TANDY, COMMODORE, TANDY, COMMODORE.",
            ";! sample_1_first = #$030f",
            ";! sample_2_first = #$1401",
            ";! sample_3_first = #$030f",
            ";! sample_4_first = #$1401",
            ";! sample_5_first = #$030f",
            "; Long seed 6818 is visibly clipped without crossing its row.",
            ";! sample_10_last = #$2b",
            "",
        ]
    )
    arguments.output.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
