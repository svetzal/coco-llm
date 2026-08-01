#!/usr/bin/env python3
"""Render a tune through the CoCo synthesizer reference to a WAV file.

The point is to hear the technique before committing any 6809 assembly. The
sample stream produced here is the same stream the player must produce on the
CoCo, so this doubles as the reference for bit-exactness checks later.
"""

from __future__ import annotations

import argparse
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from coco_synth import (
    VOICE_COUNT,
    demo_tune,
    note_increment,
    render,
    steady_tune,
    to_waveform,
)

DEFAULT_OUTPUT = ROOT / "build" / "coco-synth-demo.wav"


def write_wav(path: Path, waveform: np.ndarray, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(waveform.tobytes())


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=7300,
        help="target rate; the 6809 loop budget lands near 7300 Hz",
    )
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--tune", choices=("demo", "steady"), default="demo")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    tune = steady_tune() if arguments.tune == "steady" else demo_tune()
    dac_values = np.concatenate(
        [
            render(tune, sample_rate=arguments.sample_rate)
            for _ in range(arguments.repeats)
        ]
    )
    waveform = to_waveform(dac_values)
    write_wav(arguments.output, waveform, arguments.sample_rate)

    distinct = sorted({int(value) for value in dac_values})
    print(f"tune: {tune.name}")
    print(f"rows: {len(tune.rows)}   voices: {VOICE_COUNT}")
    print(f"ticks/row: {tune.ticks_per_row}   tick rate: {tune.tick_hz} Hz")
    print(f"sample rate: {arguments.sample_rate} Hz")
    print(f"length: {len(dac_values) / arguments.sample_rate:.2f}s")
    print(
        f"distinct DAC levels used: {len(distinct)} (range {distinct[0]}-{distinct[-1]})"
    )
    print(f"increment for A4: {note_increment(69, arguments.sample_rate)}")
    print(f"wrote {arguments.output}")


if __name__ == "__main__":
    main()
