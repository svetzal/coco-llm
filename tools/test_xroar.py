"""Prove that the real-ROM XRoar build reaches its keyboard prompt."""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
import zlib
from pathlib import Path

BASIC_11_CRC32 = 0x6270955A
EXTENDED_BASIC_10_CRC32 = 0x6111A086


def symbol_address(symbols: Path, name: str) -> int:
    contents = symbols.read_text()
    match = re.search(
        rf"^{re.escape(name)} EQU \$([0-9A-Fa-f]+)$", contents, re.MULTILINE
    )
    if match is None:
        raise ValueError(f"symbol not found: {name}")
    return int(match.group(1), 16)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xroar", required=True, type=Path)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--basic-rom", required=True, type=Path)
    parser.add_argument("--extended-basic-rom", required=True, type=Path)
    parser.add_argument("--symbols", required=True, type=Path)
    parser.add_argument("--trap-symbol", default="wait_for_key")
    parser.add_argument("--timeout", type=int, default=120)
    return parser.parse_args()


def verify_rom(path: Path, expected_crc32: int, label: str) -> None:
    actual_crc32 = zlib.crc32(path.read_bytes())
    if actual_crc32 != expected_crc32:
        raise ValueError(
            f"{label} CRC32 is {actual_crc32:08x}, expected {expected_crc32:08x}"
        )


def main() -> None:
    arguments = parse_arguments()
    trap_address = symbol_address(arguments.symbols, arguments.trap_symbol)
    verify_rom(arguments.basic_rom, BASIC_11_CRC32, "Color BASIC 1.1")
    verify_rom(
        arguments.extended_basic_rom,
        EXTENDED_BASIC_10_CRC32,
        "Extended Color BASIC 1.0",
    )

    with tempfile.TemporaryDirectory(prefix="coco-llm-xroar-") as directory:
        snapshot = Path(directory) / "wait-for-key.sna"
        command = [
            str(arguments.xroar),
            "-ui",
            "null",
            "-machine",
            "cocous",
            "-ram",
            "32",
            "-bas",
            str(arguments.basic_rom),
            "-extbas",
            str(arguments.extended_basic_rom),
            "-no-ratelimit",
            "-trap-snap",
            str(snapshot),
            "-trap",
            f"pc=0x{trap_address:04x}",
            "-timeout",
            str(arguments.timeout),
            "-quiet",
            "-run",
            str(arguments.binary),
        ]
        subprocess.run(command, check=True)
        if not snapshot.exists():
            raise RuntimeError(
                "XRoar did not reach keyboard prompt at program counter "
                f"${trap_address:04X}"
            )

    print(
        "XRoar used valid Color BASIC 1.1 / Extended Color BASIC 1.0 ROMs "
        f"and reached {arguments.trap_symbol} at program counter "
        f"${trap_address:04X}"
    )


if __name__ == "__main__":
    main()
