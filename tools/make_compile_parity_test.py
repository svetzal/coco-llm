#!/usr/bin/env python3
"""Prove the CoCo compiles rows into the same event stream the Mac does.

src/6809/steady_compile.asm mirrors src/reference/steady_synth.py's
compile_rows. This loads 128 rows into the demo's tune buffer in the
direct simulator, runs the CoCo's compiler with the demo's cursor
settings and a tempo of seven ticks a row, and asserts the stream's
length and a 16-bit sum of its bytes against the reference's compile of
the same rows. The rows are EXP-009's demo tune, four times over, which
exercises holds, note-offs, the noise voice and every decay path.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from coco_synth import demo_tune
from steady_synth import Cursor, compile_rows, encode_rows, stream_bytes

RUNNER_ORG = 0x0C00
TICKS_PER_ROW = 7
TUNE_ROWS = 128
ROW_BYTES = 12


def symbol(text: str, name: str) -> int:
    match = re.search(rf"^{re.escape(name)} EQU \$([0-9A-Fa-f]+)$", text, re.MULTILINE)
    if match is None:
        raise ValueError(f"symbol not found: {name}")
    return int(match.group(1), 16)


def decb_segments(payload: bytes) -> list[tuple[int, bytes]]:
    segments, offset = [], 0
    while offset < len(payload):
        flag = payload[offset]
        length = int.from_bytes(payload[offset + 1 : offset + 3], "big")
        address = int.from_bytes(payload[offset + 3 : offset + 5], "big")
        offset += 5
        if flag == 0xFF:
            break
        segments.append((address, payload[offset : offset + length]))
        offset += length
    return segments


def build_source(binary: Path, symbols_path: Path, sample_rate: int) -> str:
    payload = binary.read_bytes()
    symbols = symbols_path.read_text()
    address = {
        name: symbol(symbols, name)
        for name in (
            "compile_rows",
            "compile_ticks",
            "compile_end",
            "compile_overflow",
            "event_buffer",
            "tune_rows",
            "SAMPLES_PER_TICK",
            "TUNE_ROWS",
            "CURSOR_TRACK",
            "CURSOR_BLANK",
            "CURSOR_MARK",
            "CURSOR_ROWS",
        )
    }
    if address["TUNE_ROWS"] != TUNE_ROWS:
        raise ValueError(
            f"demo holds {address['TUNE_ROWS']} rows, test assumes {TUNE_ROWS}"
        )

    base = encode_rows(demo_tune())
    rows = (base * (TUNE_ROWS // len(base) + 1))[:TUNE_ROWS]
    cursor = Cursor(
        track=address["CURSOR_TRACK"],
        blank=address["CURSOR_BLANK"],
        mark=address["CURSOR_MARK"],
        rows_per_cell=address["CURSOR_ROWS"],
    )
    events = compile_rows(
        rows,
        ticks_per_row=TICKS_PER_ROW,
        samples_per_tick=address["SAMPLES_PER_TICK"],
        sample_rate=sample_rate,
        cursor=cursor,
    )
    stream = stream_bytes(events)
    checksum = sum(stream) & 0xFFFF

    row_bytes = bytes(value for row in rows for cell in row for value in cell)
    assert len(row_bytes) == TUNE_ROWS * ROW_BYTES

    lines = [
        "; Generated compile parity image. Do not edit.",
        f"; {TUNE_ROWS} rows at {TICKS_PER_ROW} ticks a row compiled on the 6809;",
        f"; the reference made {len(events)} events, {len(stream)} bytes.",
        f"        org     ${RUNNER_ORG:04X}",
        f"start   lds     #${RUNNER_ORG - 1:04X}",
        "        ldx     #rows",
        f"        ldu     #${address['tune_rows']:04X}",
        f"        ldd     #{TUNE_ROWS * ROW_BYTES}",
        "copy    pshs    d",
        "        lda     ,x+",
        "        sta     ,u+",
        "        puls    d",
        "        subd    #1",
        "        bne     copy",
        f"        lda     #{TICKS_PER_ROW}",
        f"        sta     ${address['compile_ticks']:04X}",
        f"        jsr     ${address['compile_rows']:04X}",
        "; length and sum of the stream",
        f"        ldd     ${address['compile_end']:04X}",
        f"        subd    #${address['event_buffer']:04X}",
        "        std     stream_len",
        f"        ldx     #${address['event_buffer']:04X}",
        "        ldd     #0",
        "        std     stream_sum",
        "sum     ldd     stream_sum",
        "        addb    ,x+",
        "        adca    #0",
        "        std     stream_sum",
        f"        cmpx    ${address['compile_end']:04X}",
        "        blo     sum",
        f"        lda     ${address['compile_overflow']:04X}",
        "        sta     overflow",
        "        swi",
        "",
        "stream_len rmb  2",
        "stream_sum rmb  2",
        "overflow   rmb  1",
        "rows",
    ]
    for start in range(0, len(row_bytes), 12):
        chunk = row_bytes[start : start + 12]
        lines.append("        fcb     " + ",".join(f"${byte:02X}" for byte in chunk))
    lines.append("")

    for load_address, data in decb_segments(payload):
        lines.append(f"        org     ${load_address:04X}")
        for start in range(0, len(data), 16):
            chunk = data[start : start + 16]
            lines.append(
                "        fcb     " + ",".join(f"${byte:02X}" for byte in chunk)
            )

    lines += [
        "",
        "; --- expected, computed by src/reference/steady_synth.py ---",
        f";! stream_len = #${len(stream):04X}",
        f";! stream_sum = #${checksum:04X}",
        ";! overflow = #$00",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--symbols", required=True, type=Path)
    parser.add_argument("--sample-rate", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    source = build_source(arguments.binary, arguments.symbols, arguments.sample_rate)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(source, encoding="ascii")
    print(f"rows: {TUNE_ROWS}   ticks per row: {TICKS_PER_ROW}")
    print(f"wrote {arguments.output}")


if __name__ == "__main__":
    main()
