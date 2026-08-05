#!/usr/bin/env python3
"""Measure how much of a generated melody is structure and how much is noise.

"Too random" is audible before it is arithmetic, so this puts numbers on the
things that make it sound that way, and compares them against the corpus the
model learned from. The holdout is the target: matching it is the goal, and
beating it on any of these would mean the generations are more regular than
real fiddle tunes, which is its own kind of wrong.

Three measures, all over sounded notes only:

  out-of-scale   notes not in the mode's diatonic set. Real tunes are almost
                 entirely diatonic, so a chromatic note is the single most
                 audible sign of a draw that ignored the model.
  mean step      average absolute semitone interval between notes.
  leaps          intervals over a fifth. Melodies move by step; a run of
                 large intervals is what "random" sounds like.

Also reported is the share of probability the sampler holds in its floor.
EXP_LUT floors every weight at 1 so no token is impossible, which sounds
harmless and is not: with thirty-four tokens, a confident distribution still
spends that share on a uniform draw over the whole vocabulary.
"""

from __future__ import annotations

import argparse
import json
import sys
from itertools import pairwise
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from fixed_token_lm import XorShift16
from melody_fixed import EXP_LUT, SAMPLE_SHIFT
from melody_tokens import HOLD, REST, Tune

MANIFEST = ROOT / "build" / "exp010" / "melody_model.json"
CORPUS = ROOT / "experiments" / "data" / "EXP-010-dance.jsonl"

BAR_ROWS = 8
PROGRESSION = (0, 0, 3, 4)
CHORD_ROWS = 8
METRE = 3
PAD = 34
SEED_ROWS = 16
SEED_FIGURE = [
    12,
    HOLD,
    16,
    HOLD,
    19,
    HOLD,
    16,
    HOLD,
    23,
    HOLD,
    19,
    HOLD,
    16,
    HOLD,
    12,
    HOLD,
]

MAJOR = {0, 2, 4, 5, 7, 9, 11}
MINOR = {0, 2, 3, 5, 7, 8, 10}


def weights_of(scores, shift: int, floor: int) -> list[int]:
    top = int(max(scores))
    table = [max(floor, round(np.exp(-i / 32.0) * 255)) for i in range(256)]
    return [table[min(255, (top - int(s)) >> shift)] for s in scores]


def draw(scores, random: XorShift16, shift: int, floor: int) -> int:
    weights = weights_of(scores, shift, floor)
    total = sum(weights)
    mask = 1
    while mask < total:
        mask = mask * 2 + 1
    value = total - 1
    for _ in range(16):
        candidate = random.next() & mask
        if candidate < total:
            value = candidate
            break
    running = 0
    for token, weight in enumerate(weights):
        running += weight
        if running > value:
            return token
    return len(weights) - 1


def generate(
    manifest: dict,
    seed: int,
    rows: int,
    shift: int,
    floor: int,
    mode: int,
    progression=PROGRESSION,
    chord_rows: int = CHORD_ROWS,
) -> tuple[list[int], float]:
    embeddings = [np.asarray(t, dtype=np.int64) for t in manifest["embeddings"]]
    weights = np.asarray(manifest["weights"], dtype=np.int64)
    biases = np.asarray(manifest["biases"], dtype=np.int64)
    history = [PAD] * manifest["history"]
    random = XorShift16(seed)
    tokens: list[int] = []
    floor_mass: list[float] = []

    for row in range(rows):
        beat = row % BAR_ROWS
        chord = progression[(row // chord_rows) % len(progression)]
        context = [mode, METRE, chord, beat, *history]
        if row < SEED_ROWS:
            token = SEED_FIGURE[row]
        else:
            vector = sum(embeddings[p][t] for p, t in enumerate(context))
            scores = weights @ vector + biases
            weighting = weights_of(scores, shift, floor)
            total = sum(weighting)
            floor_mass.append(sum(w for w in weighting if w <= floor) / total)
            token = draw(scores, random, shift, floor)
        tokens.append(token)
        history = history[1:] + [token]

    return tokens, float(np.mean(floor_mass)) if floor_mass else 0.0


def statistics(sequences: list[list[int]], scale: set[int]) -> dict:
    chromatic, steps, leaps, notes = 0, [], 0, 0
    for tokens in sequences:
        sounded = [t for t in tokens if t not in (HOLD, REST)]
        notes += len(sounded)
        chromatic += sum(1 for t in sounded if t % 12 not in scale)
        intervals = [abs(b - a) for a, b in pairwise(sounded)]
        steps += intervals
        leaps += sum(1 for i in intervals if i > 7)
    return {
        "notes": notes,
        "out_of_scale": 100.0 * chromatic / max(1, notes),
        "mean_step": float(np.mean(steps)) if steps else 0.0,
        "leaps": 100.0 * leaps / max(1, len(steps)),
    }


def corpus_baseline() -> dict:
    sequences, scales = [], []
    for line in CORPUS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload["split"] != "holdout":
            continue
        tune = Tune.from_json(payload)
        sequences.append(list(tune.melody))
        scales.append(MINOR if tune.mode == "minor" else MAJOR)

    chromatic, steps, leaps, notes = 0, [], 0, 0
    for tokens, scale in zip(sequences, scales):
        sounded = [t for t in tokens if t not in (HOLD, REST)]
        notes += len(sounded)
        chromatic += sum(1 for t in sounded if t % 12 not in scale)
        intervals = [abs(b - a) for a, b in pairwise(sounded)]
        steps += intervals
        leaps += sum(1 for i in intervals if i > 7)
    return {
        "notes": notes,
        "out_of_scale": 100.0 * chromatic / max(1, notes),
        "mean_step": float(np.mean(steps)),
        "leaps": 100.0 * leaps / max(1, len(steps)),
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tunes", type=int, default=60)
    parser.add_argument("--rows", type=int, default=128)
    parser.add_argument("--progression", default="0,0,3,4")
    parser.add_argument("--chord-rows", type=int, default=8)
    parser.add_argument(
        "--settings",
        default="4:1,3:1,2:1,4:0,3:0,2:0",
        help="comma-separated shift:floor pairs to compare",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    manifest = json.loads(MANIFEST.read_text())

    baseline = corpus_baseline()
    print("Real fiddle tunes (holdout) - the target, not a floor to beat")
    print(
        f"  notes {baseline['notes']}   out-of-scale "
        f"{baseline['out_of_scale']:.1f}%   mean step "
        f"{baseline['mean_step']:.2f}   leaps {baseline['leaps']:.1f}%"
    )
    print()
    print(f"Generated, {arguments.tunes} tunes of {arguments.rows} rows each")
    print(
        f"  {'shift':>5} {'floor':>5} {'out-of-scale':>13} {'mean step':>10} "
        f"{'leaps':>7} {'floor mass':>11}"
    )

    for setting in arguments.settings.split(","):
        shift, floor = (int(part) for part in setting.split(":"))
        sequences, masses = [], []
        for index in range(arguments.tunes):
            mode = index % 2
            tokens, mass = generate(
                manifest,
                0x1A2B + index * 977,
                arguments.rows,
                shift,
                floor,
                mode,
                tuple(int(c) for c in arguments.progression.split(",")),
                arguments.chord_rows,
            )
            sequences.append(tokens)
            masses.append(mass)
        # Mode alternates, so score each half against its own scale.
        major = statistics(sequences[0::2], MAJOR)
        minor = statistics(sequences[1::2], MINOR)
        notes = major["notes"] + minor["notes"]
        out = (
            major["out_of_scale"] * major["notes"]
            + minor["out_of_scale"] * minor["notes"]
        ) / notes
        step = (major["mean_step"] + minor["mean_step"]) / 2
        leaps = (major["leaps"] + minor["leaps"]) / 2
        shipped = (SAMPLE_SHIFT, min(EXP_LUT))
        marker = "  <- shipped" if (shift, floor) == shipped else ""
        print(
            f"  {shift:>5} {floor:>5} {out:>12.1f}% {step:>10.2f} "
            f"{leaps:>6.1f}% {100 * float(np.mean(masses)):>10.1f}%{marker}"
        )


if __name__ == "__main__":
    main()
