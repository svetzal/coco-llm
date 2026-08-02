#!/usr/bin/env python3
"""Continue a melody from scale degrees typed by a person.

This is the demonstration itself, on the Mac: someone enters an opening figure
as degrees — 1 2 3 4 5 6 7 3 — and the model continues it over a given chord
progression. No source tune is involved, so nothing about the continuation can
be borrowed from a corpus melody.

It is also the hardest input for the model, and deliberately so. A typed figure
is very likely a context no n-gram table in the corpus has ever seen, which is
where a table must back off and an embedding model has something to say.
"""

from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from chord_inference import scale_steps
from coco_synth import render, to_waveform
from melody_gen import arrange, generate
from melody_lm import ALL_FEATURES, MelodyConfig, MelodyModel, build_examples
from melody_tokens import HOLD, Tune, pitch_token, rows_per_bar, token_name

CORPUS = ROOT / "experiments" / "data" / "EXP-010-dance.jsonl"
SAMPLE_RATE = 5679
ROW_QUARTER_LENGTH = 0.25


def parse_degrees(text: str, mode: str, rows_each: int) -> list[int]:
    """Turn "1,2,3,4,5" into melody tokens, each held for `rows_each` rows.

    A trailing apostrophe raises a degree an octave: 1' is the octave above.
    """
    steps = scale_steps(mode)
    tokens: list[int] = []
    for item in text.replace(" ", "").split(","):
        if not item:
            continue
        octave = item.count("'")
        degree = int(item.replace("'", ""))
        if not 1 <= degree <= 7:
            raise ValueError(f"degree {degree} outside 1..7")
        token = pitch_token(steps[degree - 1] + 12 * octave)
        if token is None:
            raise ValueError(f"{item} is outside the model's pitch range")
        tokens.append(token)
        tokens.extend([HOLD] * (rows_each - 1))
    return tokens


def build_frame(
    seed: list[int], progression: list[int], mode: str, metre: str, rows: int
) -> Tune:
    """A tune-shaped frame carrying the seed, the chords and the metre."""
    bar_rows = rows_per_bar(metre, ROW_QUARTER_LENGTH)
    melody = (seed + [HOLD] * rows)[:rows]
    chords = [
        progression[(row // bar_rows) % len(progression)] - 1 for row in range(rows)
    ]
    beats = [row % bar_rows for row in range(rows)]
    return Tune(
        source="typed",
        title="typed seed",
        mode=mode,
        metre=metre,
        tonic="C",
        melody=tuple(melody),
        chords=tuple(chords),
        beats=tuple(beats),
    )


def load(path: Path) -> list[Tune]:
    return [
        Tune.from_json(json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line)["split"] == "train"
    ]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", required=True, help="degrees, e.g. 1,2,3,4,5,6,7,3")
    parser.add_argument("--mode", default="major", choices=("major", "minor"))
    parser.add_argument("--metre", default="2/4")
    parser.add_argument("--progression", default="1,1,4,5")
    parser.add_argument("--rows-each", type=int, default=2)
    parser.add_argument("--bars", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--history", type=int, default=12)
    parser.add_argument("--embedding", type=int, default=6)
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--ticks-per-row", type=int, default=7)
    parser.add_argument("--rng-seed", type=int, default=6809)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    train = load(CORPUS)
    config = MelodyConfig(
        history=arguments.history,
        embedding=arguments.embedding,
        features=ALL_FEATURES,
    )
    contexts, targets = build_examples(train, config)
    model = MelodyModel(config)
    model.train(contexts, targets, epochs=arguments.epochs)

    seed = parse_degrees(arguments.seed, arguments.mode, arguments.rows_each)
    progression = [int(v) for v in arguments.progression.split(",")]
    bar_rows = rows_per_bar(arguments.metre, ROW_QUARTER_LENGTH)
    rows = arguments.bars * bar_rows
    frame = build_frame(seed, progression, arguments.mode, arguments.metre, rows)

    rng = np.random.Generator(np.random.PCG64(arguments.rng_seed))
    melody = generate(
        model,
        config,
        frame,
        seed_rows=len(seed),
        temperature=arguments.temperature,
        rng=rng,
    )
    tune = arrange(
        melody,
        frame,
        ticks_per_row=arguments.ticks_per_row,
        bar_rows=bar_rows,
    )
    waveform = to_waveform(render(tune, sample_rate=SAMPLE_RATE))
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(arguments.output), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(waveform.tobytes())

    print(f"seed      {arguments.seed}  ({arguments.mode}, {arguments.metre})")
    print(f"entered   {' '.join(token_name(t) for t in melody[: len(seed)])}")
    print(
        f"continued {' '.join(token_name(t) for t in melody[len(seed) : len(seed) + 20])}"
    )
    onsets = sum(1 for t in melody[len(seed) :] if t != HOLD)
    print(
        f"distinct {len(set(melody[len(seed) :]))}   onsets {onsets}/{rows - len(seed)}"
    )
    print(f"wrote {arguments.output}")


if __name__ == "__main__":
    main()
