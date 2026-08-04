#!/usr/bin/env python3
"""Generate a direct-simulator parity test for EXP-011 attention scores."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
BINARY = ROOT / "build" / "coco-attention.raw"
SYMBOLS = ROOT / "build" / "coco-attention.sym"
VECTORS = ROOT / "build" / "exp011" / "test-vectors.json"
RUNNER_ORG = 0x0E00
MODEL_ORG = 0x2000


def symbol(text: str, name: str) -> int:
    match = re.search(rf"^{re.escape(name)} EQU \$([0-9A-Fa-f]+)$", text, re.MULTILINE)
    if match is None:
        raise ValueError(f"symbol not found: {name}")
    return int(match.group(1), 16)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()

    vectors = json.loads(VECTORS.read_text())
    payload = BINARY.read_bytes()
    symbols = SYMBOLS.read_text()
    address = {
        name: symbol(symbols, name)
        for name in (
            "attention_predict",
            "attention_memory_keys",
            "attention_memory_values",
            "attention_query",
            "attention_scores",
            "attention_best_slot",
            "attention_result",
        )
    }

    lines = [
        "; Generated EXP-011 parity image. Do not edit.",
        f"; {len(vectors)} novel contexts checked score by score",
        f"        org     ${RUNNER_ORG:04x}",
        f"start   lds     #${RUNNER_ORG - 1:04x}",
    ]
    expectations: list[str] = []
    for case, vector in enumerate(vectors):
        for index, key in enumerate(vector["memory_keys"]):
            lines += [
                f"        lda     #${key:02x}",
                f"        sta     ${address['attention_memory_keys'] + index:04x}",
            ]
        for index, value in enumerate(vector["memory_values"]):
            lines += [
                f"        lda     #${value:02x}",
                f"        sta     ${address['attention_memory_values'] + index:04x}",
            ]
        lines += [
            f"        lda     #${vector['query']:02x}",
            f"        sta     ${address['attention_query']:04x}",
            f"        jsr     ${address['attention_predict']:04x}",
        ]
        for index, score in enumerate(vector["scores"]):
            lines += [
                f"        ldd     ${address['attention_scores'] + 2 * index:04x}",
                f"        std     c{case}s{index}",
            ]
            expectations.append(f";! c{case}s{index} = #${score & 0xFFFF:04x}")
        lines += [
            f"        lda     ${address['attention_best_slot']:04x}",
            f"        sta     c{case}win",
            f"        lda     ${address['attention_result']:04x}",
            f"        sta     c{case}val",
        ]
        expectations += [
            f";! c{case}win = #${vector['winner']:02x}",
            f";! c{case}val = #${vector['result']:02x}",
        ]

    lines.append("        swi")
    for case in range(len(vectors)):
        for index in range(8):
            lines.append(f"c{case}s{index} rmb 2")
        lines.append(f"c{case}win rmb 1")
        lines.append(f"c{case}val rmb 1")

    lines += ["", f"        org     ${MODEL_ORG:04x}"]
    for start in range(0, len(payload), 16):
        chunk = payload[start : start + 16]
        lines.append("        fcb     " + ",".join(f"${byte:02x}" for byte in chunk))
    lines += ["", *expectations, ""]

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text("\n".join(lines), encoding="ascii")
    print(f"wrote {arguments.output}: {len(vectors)} cases, {8 * len(vectors)} scores")


if __name__ == "__main__":
    main()
