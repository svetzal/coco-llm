"""Prove that the ROM-less XRoar build reaches the model's finished loop."""

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
    return parser.parse_args()


def verify_rom(path: Path, expected_crc32: int, label: str) -> None:
    actual_crc32 = zlib.crc32(path.read_bytes())
    if actual_crc32 != expected_crc32:
        raise ValueError(
            f"{label} CRC32 is {actual_crc32:08x}, expected {expected_crc32:08x}"
        )


def main() -> None:
    arguments = parse_arguments()
    finished = symbol_address(arguments.symbols, "finished")
    verify_rom(arguments.basic_rom, BASIC_11_CRC32, "Color BASIC 1.1")
    verify_rom(
        arguments.extended_basic_rom,
        EXTENDED_BASIC_10_CRC32,
        "Extended Color BASIC 1.0",
    )

    with tempfile.TemporaryDirectory(prefix="coco-llm-xroar-") as directory:
        snapshot = Path(directory) / "finished.sna"
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
            f"pc=0x{finished:04x}",
            "-timeout",
            "120",
            "-quiet",
            "-run",
            str(arguments.binary),
        ]
        subprocess.run(command, check=True)
        if not snapshot.exists():
            raise RuntimeError(
                f"XRoar did not reach finished program counter ${finished:04X}"
            )

    print(
        "XRoar used valid Color BASIC 1.1 / Extended Color BASIC 1.0 ROMs "
        f"and reached finished program counter ${finished:04X}"
    )


if __name__ == "__main__":
    main()
