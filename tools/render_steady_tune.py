#!/usr/bin/env python3
"""Render a tune through the steady-clock reference to a WAV file.

Exactly the stream the EXP-018 player produces, event for event, on a
sample clock that never moves. Beside EXP-015's renders, which are the
same arithmetic on an idealised clock, it should sound identical; the
difference on the machine is the point of the experiment.
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
from steady_synth import compile_events, render  # noqa: E402


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
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--tune", choices=("demo", "steady"), default="demo")
    arguments = parser.parse_args()

    tune = steady_tune() if arguments.tune == "steady" else demo_tune()
    one_pass = render(tune, sample_rate=arguments.sample_rate)
    dac_values = np.concatenate([one_pass] * arguments.repeats)
    write_wav(arguments.output, to_waveform(dac_values), arguments.sample_rate)
    events = compile_events(tune, arguments.sample_rate)
    print(f"tune: {tune.name}   events: {len(events)}")
    print(f"sample rate: {arguments.sample_rate} Hz")
    print(f"length: {len(dac_values) / arguments.sample_rate:.2f}s")
    print(f"wrote {arguments.output}")


if __name__ == "__main__":
    main()
