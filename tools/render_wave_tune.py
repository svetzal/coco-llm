#!/usr/bin/env python3
"""Render a tune through the wavetable reference to a WAV file.

What the EXP-017 player should sound like, at a given rate and waveform,
to hear on the Mac before the CoCo. The stream is the reference's own, on
the player's timeline, so it is also what a capture from the machine would
be compared against.
"""

from __future__ import annotations

import argparse
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from coco_synth import demo_tune, steady_tune, to_waveform  # noqa: E402
from wave_synth import SHAPES, render  # noqa: E402


def write_wav(path: Path, waveform: np.ndarray, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(waveform.tobytes())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample-rate", type=int, required=True)
    parser.add_argument("--shape", choices=tuple(SHAPES), default="triangle")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--tune", choices=("demo", "steady"), default="demo")
    arguments = parser.parse_args()

    tune = steady_tune() if arguments.tune == "steady" else demo_tune()
    dac_values = np.concatenate(
        [
            render(tune, sample_rate=arguments.sample_rate, shape=arguments.shape)
            for _ in range(arguments.repeats)
        ]
    )
    write_wav(arguments.output, to_waveform(dac_values), arguments.sample_rate)
    distinct = sorted({int(value) for value in dac_values})
    print(f"tune: {tune.name}   shape: {arguments.shape}")
    print(f"sample rate: {arguments.sample_rate} Hz")
    print(f"length: {len(dac_values) / arguments.sample_rate:.2f}s")
    print(f"distinct DAC levels used: {len(distinct)} (range {distinct[0]}-{distinct[-1]})")
    print(f"wrote {arguments.output}")


if __name__ == "__main__":
    main()
