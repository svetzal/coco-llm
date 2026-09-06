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
# The 32 KiB Super Extended Color BASIC image XRoar loads for a CoCo 3.
COCO3_ROM_CRC32 = 0xB4C88D6C


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
    parser.add_argument("--basic-rom", type=Path)
    parser.add_argument("--extended-basic-rom", type=Path)
    parser.add_argument(
        "--machine",
        choices=("cocous", "coco3", "coco3h"),
        default="cocous",
        help="coco3 is a CoCo 3 with a 6809, coco3h one with a 6309; both take "
        "--coco3-rom instead of the two CoCo 1 ROMs",
    )
    parser.add_argument("--coco3-rom", type=Path, help="the 32 KiB CoCo 3 ROM")
    parser.add_argument(
        "--ram-init",
        choices=("clear", "set", "pattern", "random"),
        default=None,
        help="what XRoar fills RAM with at power-on. 'set' (all ones) is the "
        "hostile choice: a program that only works because a cell it never "
        "wrote happened to be zero fails here instead of on the machine",
    )
    parser.add_argument("--symbols", required=True, type=Path)
    parser.add_argument("--trap-symbol", default="wait_for_key")
    parser.add_argument("--ram", choices=(16, 32, 64), type=int, default=32)
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
    if arguments.machine == "cocous":
        if arguments.basic_rom is None or arguments.extended_basic_rom is None:
            raise SystemExit("cocous needs --basic-rom and --extended-basic-rom")
        verify_rom(arguments.basic_rom, BASIC_11_CRC32, "Color BASIC 1.1")
        verify_rom(
            arguments.extended_basic_rom,
            EXTENDED_BASIC_10_CRC32,
            "Extended Color BASIC 1.0",
        )
        machine_options = [
            "-ram", str(arguments.ram),
            "-bas", str(arguments.basic_rom),
            "-extbas", str(arguments.extended_basic_rom),
        ]
        rom_note = "valid Color BASIC 1.1 / Extended Color BASIC 1.0 ROMs"
    else:
        if arguments.coco3_rom is None:
            raise SystemExit(f"{arguments.machine} needs --coco3-rom")
        verify_rom(arguments.coco3_rom, COCO3_ROM_CRC32, "CoCo 3 ROM")
        machine_options = ["-extbas", str(arguments.coco3_rom)]
        rom_note = "a valid CoCo 3 ROM"
    if arguments.ram_init:
        machine_options += ["-ram-init", arguments.ram_init]
        rom_note += f", RAM {arguments.ram_init} at power-on"

    with tempfile.TemporaryDirectory(prefix="coco-llm-xroar-") as directory:
        snapshot = Path(directory) / "wait-for-key.sna"
        command = [
            str(arguments.xroar),
            "-ui",
            "null",
            "-machine",
            arguments.machine,
            *machine_options,
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
        f"XRoar ({arguments.machine}) used {rom_note} "
        f"and reached {arguments.trap_symbol} at program counter "
        f"${trap_address:04X}"
    )


if __name__ == "__main__":
    main()
