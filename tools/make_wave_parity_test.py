#!/usr/bin/env python3
"""Prove the wavetable player's sample loop matches the Python reference.

The EXP-009 parity test, pointed at the EXP-017 player. A known voice
configuration runs a fixed number of samples through the real loop in the
direct simulator, and the phase accumulators, LFSR and final DAC byte are
asserted against src/reference/wave_synth.py.

With --shape square the expected DAC byte is also checked against the
EXP-009 formula, so the table player is shown to reproduce the masked-bit
player exactly before any other shape is trusted.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from coco_synth import VOICE_COUNT, Voice, note_increment  # noqa: E402
from wave_synth import SHAPES, wave_table  # noqa: E402

RUNNER_ORG = 0x1000
SAMPLES = 200
SAMPLE_RATE = 5789
VSTATE_STRIDE = 3

NOTES = (45, 57, 69, 96)
VOLUMES = (12, 13, 6, 11)
NOISE = (False, False, False, True)


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


def expected_state(shape: str) -> tuple[list[Voice], int]:
    table = wave_table(shape)
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

    dac = 0
    for index, voice in enumerate(voices):
        if voice.noise:
            dac += (VOLUMES[index] << 2) if voice.bit else 0
        else:
            dac += table[VOLUMES[index]][voice.phase >> 8] << 2

    if shape == "square":
        masked = sum(
            (VOLUMES[index] << 2)
            for index, voice in enumerate(voices)
            if voice.bit
        )
        if masked != dac:
            raise AssertionError(
                f"square table gives {dac:#04x}, EXP-009's mask gives {masked:#04x}"
            )
    return voices, dac & 0xFF


def build_source(binary: Path, symbols_path: Path, shape: str) -> str:
    payload = binary.read_bytes()
    symbols = symbols_path.read_text()
    address = {
        name: symbol_address(symbols, name)
        for name in (
            "vstate",
            "incrs",
            "scaled",
            "decays",
            "lfsr",
            "dac_acc",
            "tick_samples",
            "row_ticks",
            "rows_left",
            "finished",
            "cells_left",
            "decay_left",
            "play_tune",
            "wave_table",
        )
    }
    if address["wave_table"] & 0xFF:
        raise ValueError("wave_table is not on a 256-byte boundary")
    page = address["wave_table"] >> 8
    voices, dac = expected_state(shape)

    lines = [
        "; Generated parity image. Do not edit.",
        f"; {SAMPLES} samples at {SAMPLE_RATE} Hz through the wavetable loop, {shape}.",
        f"        org     ${RUNNER_ORG:04X}",
        f"start   lds     #${RUNNER_ORG - 1:04X}",
        "        lda     #$20",
        "        tfr     a,dp",
    ]

    for index in range(VOICE_COUNT):
        increment = note_increment(NOTES[index], SAMPLE_RATE)
        state = address["vstate"] + index * VSTATE_STRIDE
        lines += [
            f"        ldd     #${increment:04X}",
            f"        std     ${address['incrs'] + index * 2:04X}",
            f"        lda     #${page + VOLUMES[index]:02X}",
            f"        sta     ${state:04X}",
            "        ldd     #$0000",
            f"        std     ${state + 1:04X}",
            f"        lda     #${VOLUMES[index] << 2:02X}",
            f"        sta     ${address['scaled'] + index:04X}",
            "        clra",
            f"        sta     ${address['decays'] + index:04X}",
        ]

    lines += [
        "        ldd     #$ACE1",
        f"        std     ${address['lfsr']:04X}",
        "        clra",
        f"        sta     ${address['dac_acc']:04X}",
        f"        sta     ${address['finished']:04X}",
        f"        sta     ${address['rows_left']:04X}",
        f"        sta     ${address['cells_left']:04X}",
        f"        sta     ${address['decay_left']:04X}",
        "        lda     #$01",
        f"        sta     ${address['row_ticks']:04X}",
        f"        lda     #${SAMPLES:02X}",
        f"        sta     ${address['tick_samples']:04X}",
        f"        jsr     ${address['play_tune']:04X}",
        "        swi",
        "",
    ]

    for load_address, data in decb_segments(payload):
        lines.append(f"        org     ${load_address:04X}")
        for start in range(0, len(data), 16):
            chunk = data[start : start + 16]
            lines.append(
                "        fcb     " + ",".join(f"${byte:02X}" for byte in chunk)
            )

    lines += ["", "; --- expected state, computed by src/reference/wave_synth.py ---"]
    for index in range(VOICE_COUNT - 1):
        phase_at = address["vstate"] + index * VSTATE_STRIDE + 1
        lines.append(f"phase{index} equ ${phase_at:04X}")
    lines.append(f"lfsr_at equ ${address['lfsr']:04X}")
    lines.append("dac_port equ $FF20")

    lines.append("")
    for index in range(VOICE_COUNT - 1):
        lines.append(f";! phase{index} = #${voices[index].phase:04X}")
    lines.append(f";! lfsr_at = #${voices[3].lfsr:04X}")
    lines.append(f";! dac_port = #${dac:02X}")
    lines.append("")
    return "\n".join(lines)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--symbols", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--shape", choices=tuple(SHAPES), default="triangle")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    source = build_source(arguments.binary, arguments.symbols, arguments.shape)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(source, encoding="ascii")
    print(f"shape: {arguments.shape}   samples: {SAMPLES}   rate: {SAMPLE_RATE} Hz")
    print(f"wrote {arguments.output}")


if __name__ == "__main__":
    main()
