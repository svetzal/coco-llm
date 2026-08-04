#!/usr/bin/env python3
"""Generate a direct-simulator state and screen test for EXP-011's UI."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
BINARY = ROOT / "build" / "coco-attention.raw"
SYMBOLS = ROOT / "build" / "coco-attention.sym"
MANIFEST = ROOT / "build" / "exp011" / "manifest.json"
RUNNER_ORG = 0x0C00
MODEL_ORG = 0x2000
SCREEN = 0x0400


def symbol(text: str, name: str) -> int:
    match = re.search(rf"^{re.escape(name)} EQU \$([0-9A-Fa-f]+)$", text, re.MULTILINE)
    if match is None:
        raise ValueError(f"symbol not found: {name}")
    return int(match.group(1), 16)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    payload = BINARY.read_bytes()
    symbols = SYMBOLS.read_text()
    address = {
        name: symbol(symbols, name)
        for name in (
            "attention_ui_initialize",
            "attention_ui_ask",
            "attention_ui_next_context",
            "attention_ui_slow_step",
            "attention_ui_context_index",
            "attention_ui_selected_slot",
            "attention_ui_has_answer",
            "attention_ui_slow_index",
            "attention_ui_slow_best_valid",
            "attention_ui_slow_best_slot",
            "attention_query",
            "attention_result",
            "attention_best_slot",
            "attention_memory_values",
        )
    }
    model_id = manifest["model_id"]
    model_chars = [ord(character) | 0x40 for character in model_id]

    lines = [
        "; Generated EXP-011 UI test. Do not edit.",
        f"        org     ${RUNNER_ORG:04x}",
        f"start   lds     #${RUNNER_ORG - 1:04x}",
        f"        jsr     ${address['attention_ui_initialize']:04x}",
        f"        lda     ${address['attention_ui_selected_slot']:04x}",
        "        sta     initialslot",
        f"        lda     ${address['attention_query']:04x}",
        "        sta     initialquery",
        f"        lda     ${SCREEN:04x}",
        "        sta     titlechar",
    ]
    for index in range(4):
        lines += [
            f"        lda     ${SCREEN + 32 + 6 + index:04x}",
            f"        sta     modelchar{index}",
        ]
    lines += [
        f"        jsr     ${address['attention_ui_ask']:04x}",
        f"        lda     ${SCREEN:04x}",
        "        sta     answertitle",
        f"        lda     ${address['attention_best_slot']:04x}",
        "        sta     firstslot",
        f"        lda     ${address['attention_result']:04x}",
        "        sta     firstvalue",
        f"        lda     ${SCREEN + 7 * 32 + 2:04x}",
        "        sta     firstmarker",
        f"        lda     ${SCREEN + 9 * 32 + 13:04x}",
        "        sta     firstanswer",
        f"        jsr     ${address['attention_ui_next_context']:04x}",
        f"        lda     ${SCREEN:04x}",
        "        sta     changedtitle",
        f"        lda     ${address['attention_ui_context_index']:04x}",
        "        sta     nextcontext",
        f"        lda     ${address['attention_query']:04x}",
        "        sta     keptquery",
        f"        lda     ${address['attention_ui_selected_slot']:04x}",
        "        sta     relocated",
        f"        lda     ${address['attention_memory_values'] + 3:04x}",
        "        sta     newbinding",
        f"        lda     ${address['attention_ui_has_answer']:04x}",
        "        sta     cleared",
        f"        jsr     ${address['attention_ui_ask']:04x}",
        f"        lda     ${address['attention_result']:04x}",
        "        sta     secondvalue",
        f"        clr     ${address['attention_ui_slow_index']:04x}",
        f"        clr     ${address['attention_ui_slow_best_valid']:04x}",
    ]
    for _ in range(8):
        lines.append(f"        jsr     ${address['attention_ui_slow_step']:04x}")
    lines += [
        f"        lda     ${address['attention_ui_slow_best_slot']:04x}",
        "        sta     slowwinner",
        "        swi",
        "initialslot rmb 1",
        "initialquery rmb 1",
        "titlechar rmb 1",
        "modelchar0 rmb 1",
        "modelchar1 rmb 1",
        "modelchar2 rmb 1",
        "modelchar3 rmb 1",
        "answertitle rmb 1",
        "firstslot rmb 1",
        "firstvalue rmb 1",
        "firstmarker rmb 1",
        "firstanswer rmb 1",
        "changedtitle rmb 1",
        "nextcontext rmb 1",
        "keptquery rmb 1",
        "relocated rmb 1",
        "newbinding rmb 1",
        "cleared rmb 1",
        "secondvalue rmb 1",
        "slowwinner rmb 1",
        "",
        f"        org     ${MODEL_ORG:04x}",
    ]
    for start in range(0, len(payload), 16):
        chunk = payload[start : start + 16]
        lines.append("        fcb     " + ",".join(f"${byte:02x}" for byte in chunk))
    lines += [
        "",
        ";! initialslot = #$01",
        ";! initialquery = #$01",
        ";! titlechar = #$31",
        *[
            f";! modelchar{index} = #${value:02x}"
            for index, value in enumerate(model_chars)
        ],
        ";! answertitle = #$32",
        ";! firstslot = #$01",
        ";! firstvalue = #$02",
        ";! firstmarker = #$2a",
        ";! firstanswer = #$32",
        ";! changedtitle = #$33",
        ";! nextcontext = #$01",
        ";! keptquery = #$01",
        ";! relocated = #$03",
        ";! newbinding = #$06",
        ";! cleared = #$00",
        ";! secondvalue = #$06",
        ";! slowwinner = #$03",
        "",
    ]

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text("\n".join(lines), encoding="ascii")
    print(f"wrote {arguments.output}")


if __name__ == "__main__":
    main()
