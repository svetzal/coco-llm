#!/usr/bin/env python3
"""Run the multiply benchmark under XRoar and report what the machine measured.

The program leaves its results in registers at bench_trap. XRoar's instruction
trace prints the registers with each instruction, so trapping there and tracing
one instruction yields every number on a single line. This replaced reading the
results out of a trap snapshot, which returned an empty machine often enough
not to be trusted.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

TICKS_PER_SECOND = 60.0


def symbol_address(symbols: Path, name: str) -> int:
    match = re.search(
        rf"^{re.escape(name)} EQU \$([0-9A-Fa-f]+)$",
        symbols.read_text(),
        re.MULTILINE,
    )
    if match is None:
        raise ValueError(f"symbol not found: {name}")
    return int(match.group(1), 16)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xroar", default="xroar")
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--symbols", required=True, type=Path)
    parser.add_argument("--basic-rom", required=True, type=Path)
    parser.add_argument("--extended-basic-rom", required=True, type=Path)
    parser.add_argument("--cpu", choices=("6809", "6309"), default="6809")
    parser.add_argument("--timeout", type=int, default=300)
    arguments = parser.parse_args()

    trap = symbol_address(arguments.symbols, "bench_trap")
    expected = symbol_address(arguments.symbols, "BENCH_EXPECTED")
    count = symbol_address(arguments.symbols, "BENCH_COUNT")
    passes = symbol_address(arguments.symbols, "BENCH_PASSES")

    command = [
        arguments.xroar,
        "-ui",
        "null",
        "-machine",
        "cocous",
        "-machine-cpu",
        arguments.cpu,
        "-ram",
        "64",
        "-bas",
        str(arguments.basic_rom),
        "-extbas",
        str(arguments.extended_basic_rom),
        "-no-ratelimit",
        "-timeout",
        str(arguments.timeout),
        "-quiet",
        "-trap",
        f"pc=0x{trap:04x}",
        "-trap-trace-n",
        "1",
        # Without this XRoar keeps running to -timeout after the trap fires.
        "-trap-timeout",
        "1",
        "-run",
        str(arguments.binary),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    match = re.search(
        r"^[0-9a-f]{4}\|.*a=([0-9a-f]{2}) b=([0-9a-f]{2}).*"
        r"x=([0-9a-f]{4}) y=([0-9a-f]{4}) u=([0-9a-f]{4})",
        completed.stdout,
        re.MULTILINE,
    )
    if match is None:
        raise SystemExit("XRoar did not reach bench_trap:\n" + completed.stdout[-2000:])

    a, b, emulation, native, muld = (int(g, 16) for g in match.groups())
    checksum = (a << 8) | b
    multiplies = count * passes

    print(
        f"{multiplies:,} multiplications over {count} trained parameters, "
        f"{arguments.cpu} CPU"
    )
    rows = [("6809 kernel, 6809 mode", emulation)]
    if native:
        rows.append(("6809 kernel, native mode", native))
    if muld:
        # The fallback build runs MULD without entering native mode, and it is
        # the absence of the native row that says so.
        mode = "native mode" if native else "6809 mode"
        rows.append((f"MULD kernel, {mode}", muld))
    for label, ticks in rows:
        seconds = ticks / TICKS_PER_SECOND
        cycles = seconds * 895_000 / multiplies
        share = emulation / ticks
        print(
            f"  {label:<26} {ticks:5d} ticks  {seconds:6.2f} s  "
            f"{cycles:6.1f} cycles each  {share:.2f}x"
        )

    if checksum != expected:
        raise SystemExit(
            f"checksum ${checksum:04X} does not match the reference ${expected:04X}"
        )
    print(f"  checksum ${checksum:04X} matches the Python reference")


if __name__ == "__main__":
    main()
