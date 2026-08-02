#!/usr/bin/env python3
"""Generate a melody, arrange it, and render it as the CoCo would play it.

Phase A showed the model predicts held-out chorale melodies better than any
table that fits the machine. This asks the different question the demonstration
actually rests on: does it *generate* anything worth hearing?

Rendered at the player's real sample rate, so what comes out is what the CoCo
would produce, not an idealised version of it.
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

from coco_synth import render, to_waveform
from melody_gen import arrange, generate
from melody_lm import ALL_FEATURES, MelodyConfig, MelodyModel, build_examples
from melody_tokens import Tune, rows_per_bar, token_name

CHORALES = ROOT / "experiments" / "data" / "EXP-010-chorales.jsonl"
SAMPLE_RATE = 5679  # the frozen player's measured rate


def load(path: Path) -> tuple[list[Tune], list[Tune]]:
    train, holdout = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        target = holdout if payload["split"] == "holdout" else train
        target.append(Tune.from_json(payload))
    return train, holdout


def write_wav(path: Path, waveform: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(waveform.tobytes())


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=CHORALES)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--history", type=int, default=18)
    parser.add_argument("--embedding", type=int, default=6)
    parser.add_argument("--features", type=str, default="all")
    parser.add_argument("--tune", type=int, default=0, help="index into the holdout")
    parser.add_argument("--seed-bars", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--ticks-per-row", type=int, default=12)
    parser.add_argument("--rows", type=int, default=96)
    parser.add_argument("--diatonic-only", action="store_true")
    parser.add_argument("--no-drums", action="store_true")
    parser.add_argument(
        "--use-source",
        action="store_true",
        help="render Bach's own continuation instead, same arrangement",
    )
    parser.add_argument("--rng-seed", type=int, default=6809)
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "generated.wav")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    train, holdout = load(arguments.corpus)
    features = (
        ALL_FEATURES
        if arguments.features == "all"
        else tuple(f for f in arguments.features.split(",") if f)
    )
    config = MelodyConfig(
        history=arguments.history,
        embedding=arguments.embedding,
        features=features,
    )

    print(f"training {config.parameters} parameters for {arguments.epochs} epochs")
    contexts, targets = build_examples(train, config)
    model = MelodyModel(config)
    model.train(contexts, targets, epochs=arguments.epochs)

    source = holdout[arguments.tune % len(holdout)]
    row_ql = 0.25 if "dance" in arguments.corpus.name else 0.5
    bar_rows = rows_per_bar(source.metre, row_ql)
    limit = min(arguments.rows, source.rows)
    source = Tune(
        source=source.source,
        title=source.title,
        mode=source.mode,
        metre=source.metre,
        tonic=source.tonic,
        melody=source.melody[:limit],
        chords=source.chords[:limit],
        beats=source.beats[:limit],
    )
    seed_rows = arguments.seed_bars * bar_rows

    rng = np.random.Generator(np.random.PCG64(arguments.rng_seed))
    if arguments.use_source:
        melody = list(source.melody)
    else:
        melody = generate(
            model,
            config,
            source,
            seed_rows=seed_rows,
            temperature=arguments.temperature,
            rng=rng,
            diatonic_only=arguments.diatonic_only,
        )

    tune = arrange(
        melody,
        source,
        ticks_per_row=arguments.ticks_per_row,
        bar_rows=bar_rows,
        drums=not arguments.no_drums,
    )
    waveform = to_waveform(render(tune, sample_rate=SAMPLE_RATE))
    write_wav(arguments.output, waveform)

    rate = 50.0 / arguments.ticks_per_row
    distinct = len(set(melody[seed_rows:]))
    print(f"\nsource:  {source.title}  ({source.mode}, {source.metre})")
    print(f"seed:    {' '.join(token_name(t) for t in melody[:seed_rows])}")
    print(
        f"given:   {' '.join(token_name(t) for t in source.melody[seed_rows : seed_rows + 16])}"
    )
    print(
        f"model:   {' '.join(token_name(t) for t in melody[seed_rows : seed_rows + 16])}"
    )
    print(
        f"\ndistinct tokens generated: {distinct}   temperature {arguments.temperature}"
    )
    print(f"tempo: {rate:.1f} rows/s, eighth notes -> {rate * 30:.0f} BPM")
    print(f"length: {tune.seconds:.1f}s")
    print(f"wrote {arguments.output}")


if __name__ == "__main__":
    main()
