#!/usr/bin/env python3
"""Wrap an LWASM raw binary in source the direct simulator understands.

The simulator assembles what it is given and has no include directive, so the
real assembly is done by lwasm and the resulting bytes are handed over as data
with symbol equates beside them. Deliberately generic: it takes the assertions
on the command line rather than knowing anything about this benchmark.
"""

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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--symbols", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--assert", dest="assertions", action="append", default=[],
        metavar="SYMBOL=VALUE",
        help="a criterion, for example bench_sum=#$d636",
    )
    parser.add_argument(
        "--assert-symbol", dest="symbol_assertions", action="append", default=[],
        metavar="SYMBOL=EXPECTED",
        help="compare a location against another symbol's value, so the "
             "expected number comes from the build rather than being retyped",
    )
    arguments = parser.parse_args()

    payload = arguments.binary.read_bytes()
    symbols = arguments.symbols.read_text()
    start = symbol_address(symbols, "start")

    for assertion in arguments.symbol_assertions:
        name, _, expected = assertion.partition("=")
        value = symbol_address(symbols, expected)
        arguments.assertions.append(f"{name}=#${value:04x}")

    lines = [
        "; Generated direct-simulator image. Do not edit.",
        f"        org     ${start:04x}",
    ]
    for offset in range(0, len(payload), 16):
        values = ",".join(f"${value:02x}" for value in payload[offset:offset + 16])
        lines.append(f"        fcb     {values}")
    lines.append("")

    for assertion in arguments.assertions:
        name, _, value = assertion.partition("=")
        address = symbol_address(symbols, name)
        lines.append(f"{name:<20} equ     ${address:04x}")
    lines.append("")
    for assertion in arguments.assertions:
        name, _, value = assertion.partition("=")
        lines.append(f";! {name} = {value}")
    lines.append("")

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
