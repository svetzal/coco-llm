"""Prove that the ROM-less XRoar build reaches the model's finished loop."""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from pathlib import Path


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
    parser.add_argument("--rom", required=True, type=Path)
    parser.add_argument("--symbols", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    finished = symbol_address(arguments.symbols, "finished")

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
            "-no-bas",
            "-no-extbas",
            "-cart",
            "coco-llm",
            "-cart-type",
            "rom",
            "-cart-rom",
            str(arguments.rom),
            "-cart-autorun",
            "-machine-cart",
            "coco-llm",
            "-no-ratelimit",
            "-trap-snap",
            str(snapshot),
            "-trap",
            f"pc=0x{finished:04x}",
            "-timeout",
            "2",
            "-quiet",
        ]
        subprocess.run(command, check=True)
        if not snapshot.exists():
            raise RuntimeError(
                f"XRoar did not reach finished program counter ${finished:04X}"
            )

    print(f"XRoar reached finished program counter ${finished:04X}")


if __name__ == "__main__":
    main()
