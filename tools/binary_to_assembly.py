"""Convert a binary payload into an LWASM FCB include file."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    payload = arguments.input.read_bytes()
    lines = ["; Generated binary payload. Do not edit.", "payload"]
    for offset in range(0, len(payload), 16):
        values = ",".join(f"${value:02x}" for value in payload[offset : offset + 16])
        lines.append(f"        fcb     {values}")
    lines.extend(["payload_end", ""])
    arguments.output.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
