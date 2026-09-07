#!/usr/bin/env python3
"""Prove the steady player's sample loop matches EXP-009's arithmetic.

The EXP-009 parity test, pointed at the EXP-018 player: a known voice
configuration, a fixed number of samples through the real loop in the
direct simulator, then the phase accumulators, LFSR and final DAC byte
asserted against the reference. The runner supplies a one-event stream:
a wait of the sample count, then the event that sets `finished`.

It also checks the assembled direct-page layout against the offsets
src/reference/steady_synth.py compiles the stream for.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from coco_synth import VOICE_COUNT, Voice, note_increment  # noqa: E402
from steady_synth import (  # noqa: E402
    DAC_ACC,
    FINISHED,
    INCRS,
    LFSR,
    PHASES,
    SCALED,
    SCRATCH,
    TICK_SAMPLES,
)

RUNNER_ORG = 0x1000
PAGE = 0x2000
SAMPLES = 200
SAMPLE_RATE = 4566

NOTES = (45, 57, 69, 96)
VOLUMES = (12, 13, 6, 11)
NOISE = (False, False, False, True)

LAYOUT = {
    "phases": PHASES,
    "incrs": INCRS,
    "scaled": SCALED,
    "dac_acc": DAC_ACC,
    "lfsr": LFSR,
    "tick_samples": TICK_SAMPLES,
    "finished": FINISHED,
    "scratch": SCRATCH,
}


def symbol_address(symbols: str, name: str) -> int:
    match = re.search(
        rf"^{re.escape(name)} EQU \$([0-9A-Fa-f]+)$", symbols, re.MULTILINE
    )
    if match is None:
        raise ValueError(f"symbol not found: {name}")
    return int(match.group(1), 16)


def decb_segments(payload: bytes) -> list[tuple[int, bytes]]:
    segments: list[tuple[int, bytes]] = []
    offset = 0
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


def expected_state() -> tuple[list[Voice], int]:
    voices = [
        Voice(
            increment=note_increment(NOTES[index], SAMPLE_RATE),
            noise=NOISE[index],
        )
        for index in range(VOICE_COUNT)
    ]
    for _ in range(SAMPLES):
        for voice in voices:
            voice.step()
    dac = sum((VOLUMES[index] << 2) for index, voice in enumerate(voices) if voice.bit)
    return voices, dac & 0xFF


def build_source(binary: Path, symbols_path: Path) -> str:
    payload = binary.read_bytes()
    symbols = symbols_path.read_text()
    for name, offset in LAYOUT.items():
        found = symbol_address(symbols, name)
        if found != PAGE + offset:
            raise ValueError(
                f"{name} assembled at ${found:04X}, reference expects ${PAGE + offset:04X}"
            )
    ev_ptr = symbol_address(symbols, "ev_ptr")
    play_tune = symbol_address(symbols, "play_tune")
    voices, dac = expected_state()

    lines = [
        "; Generated parity image. Do not edit.",
        f"; {SAMPLES} samples at {SAMPLE_RATE} Hz through the steady loop.",
        f"        org     ${RUNNER_ORG:04X}",
        f"start   lds     #${RUNNER_ORG - 1:04X}",
        "        lda     #$20",
        "        tfr     a,dp",
    ]
    for index in range(VOICE_COUNT):
        increment = note_increment(NOTES[index], SAMPLE_RATE)
        lines += [
            f"        ldd     #${increment:04X}",
            f"        std     ${PAGE + INCRS + index * 2:04X}",
            "        ldd     #$0000",
            f"        std     ${PAGE + PHASES + index * 2:04X}",
            f"        lda     #${VOLUMES[index] << 2:02X}",
            f"        sta     ${PAGE + SCALED + index:04X}",
        ]
    lines += [
        "        ldd     #$ACE1",
        f"        std     ${PAGE + LFSR:04X}",
        "        clra",
        f"        sta     ${PAGE + DAC_ACC:04X}",
        f"        sta     ${PAGE + FINISHED:04X}",
        "        ldd     #stream",
        f"        std     ${ev_ptr:04X}",
        f"        jsr     ${play_tune:04X}",
        "        swi",
        "",
        "; wait SAMPLES, then the event that sets finished, then a spare wait",
        f"stream  fcb     ${SAMPLES:02X},${(PAGE + FINISHED) >> 8:02X},"
        f"${(PAGE + FINISHED) & 0xFF:02X},$01,$00",
        "",
    ]

    for load_address, data in decb_segments(payload):
        lines.append(f"        org     ${load_address:04X}")
        for start in range(0, len(data), 16):
            chunk = data[start : start + 16]
            lines.append(
                "        fcb     " + ",".join(f"${byte:02X}" for byte in chunk)
            )

    lines += ["", "; --- expected state, computed by src/reference/coco_synth.py ---"]
    for index in range(VOICE_COUNT - 1):
        lines.append(f"phase{index} equ ${PAGE + PHASES + index * 2:04X}")
    lines.append(f"lfsr_at equ ${PAGE + LFSR:04X}")
    lines.append("dac_port equ $FF20")
    lines.append("")
    for index in range(VOICE_COUNT - 1):
        lines.append(f";! phase{index} = #${voices[index].phase:04X}")
    lines.append(f";! lfsr_at = #${voices[3].lfsr:04X}")
    lines.append(f";! dac_port = #${dac:02X}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--symbols", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    source = build_source(arguments.binary, arguments.symbols)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(source, encoding="ascii")
    print(f"samples: {SAMPLES}   rate: {SAMPLE_RATE} Hz")
    print(f"wrote {arguments.output}")


if __name__ == "__main__":
    main()
