#!/usr/bin/env python3
"""Reduce Bach chorales to the EXP-009 player's row grid.

For each chorale this emits, one token per row: the soprano melody as
semitones above the tonic, the chord root as a scale degree taken from the
harmony the other three voices actually state, and the position within the
bar. Mode, metre and tonic are recorded per tune.

The harmony is read, not guessed. That matters because the experiment's
secondary hypothesis is about harmonic conditioning, and testing it against
inferred chords would mostly measure the inference.

One trap is guarded here. music21's `Key.getScale()` returns the scale of the
key *signature*, so for G minor it hands back B flat major. Every minor
chorale would then be encoded a third out, plausibly enough that nothing would
look wrong. The scale is built from the key's own tonic and mode instead.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from melody_tokens import (
    HOLD,
    METRES,
    REST,
    ROW_QUARTER_LENGTH,
    Tune,
    chord_token,
    describe,
    pitch_token,
    rows_per_bar,
)

DEFAULT_OUTPUT = ROOT / "experiments" / "data" / "EXP-010-chorales.jsonl"
HOLDOUT_EVERY = 6  # every sixth chorale is held out, as a whole tune


def tonic_below(tonic_pitch_class: int, lowest_midi: int) -> int:
    """The tonic in the octave at or below the melody's lowest note."""
    candidate = tonic_pitch_class
    while candidate + 12 <= lowest_midi:
        candidate += 12
    while candidate > lowest_midi:
        candidate -= 12
    return candidate


def extract(score, source: str):
    from music21 import roman
    from music21 import scale as m21scale

    key = score.analyze("key")
    if key.mode not in ("major", "minor"):
        return None, f"unsupported mode {key.mode}"

    signatures = list(score.parts[0].recurse().getElementsByClass("TimeSignature"))
    if not signatures:
        return None, "no time signature"
    metre = signatures[0].ratioString
    if metre not in METRES:
        return None, f"unsupported metre {metre}"
    if len({s.ratioString for s in signatures}) > 1:
        return None, "changes metre"

    soprano = score.parts[0].flatten().notesAndRests.stream()
    notes = [element for element in soprano if element.isNote]
    if not notes:
        return None, "no melody notes"

    # music21's Key.getScale() would return the key signature's major scale,
    # so the scale is built from the key's own tonic and mode. Pitch is encoded
    # as a semitone offset, which does not need the scale object, but building
    # it here keeps the guard visible next to the code it protects.
    m21scale.MajorScale(key.tonic) if key.mode == "major" else m21scale.MinorScale(
        key.tonic
    )

    lowest = min(note.pitch.midi for note in notes)
    tonic_midi = tonic_below(key.tonic.pitchClass, lowest)

    harmony = score.chordify()
    chords = harmony.flatten().getElementsByClass("Chord").stream()

    end = float(soprano.highestTime)
    bar_rows = rows_per_bar(metre)

    melody: list[int] = []
    chord_row: list[int] = []
    beats: list[int] = []
    onsets = {round(float(note.offset) / ROW_QUARTER_LENGTH): note for note in notes}

    row_count = round(end / ROW_QUARTER_LENGTH)
    sounding = False
    for row in range(row_count):
        offset = row * ROW_QUARTER_LENGTH

        note = onsets.get(row)
        if note is not None:
            token = pitch_token(note.pitch.midi - tonic_midi)
            if token is None:
                return None, f"melody leaves the pitch range at row {row}"
            melody.append(token)
            sounding = True
        else:
            element = soprano.getElementAtOrBefore(offset)
            if element is None or element.isRest:
                melody.append(REST)
                sounding = False
            else:
                melody.append(HOLD if sounding else REST)

        current = chords.getElementAtOrBefore(offset)
        if current is None:
            return None, f"no harmony at row {row}"
        try:
            degree = roman.romanNumeralFromChord(current, key).scaleDegree
            chord_row.append(chord_token(degree))
        except Exception:  # noqa: BLE001 - music21 raises broadly here
            return None, f"unreadable harmony at row {row}"

        beats.append(row % bar_rows)

    return (
        Tune(
            source=source,
            title=str(score.metadata.title or source),
            mode=key.mode,
            metre=metre,
            tonic=key.tonic.name,
            melody=tuple(melody),
            chords=tuple(chord_row),
            beats=tuple(beats),
        ),
        None,
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=0, help="0 means all")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    from music21 import corpus

    scores = list(corpus.chorales.Iterator(numberingSystem="bwv"))
    if arguments.limit:
        scores = scores[: arguments.limit]

    tunes: list[Tune] = []
    rejected: Counter[str] = Counter()
    for index, score in enumerate(scores):
        source = f"bach/bwv{score.metadata.title or index}"
        try:
            tune, reason = extract(score, source)
        except Exception as error:  # noqa: BLE001 - record and continue
            tune, reason = None, f"{type(error).__name__}"
        if tune is None:
            rejected[reason or "unknown"] += 1
            continue
        tunes.append(tune)

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("w", encoding="utf-8") as handle:
        for index, tune in enumerate(tunes):
            payload = tune.to_json()
            payload["split"] = "holdout" if index % HOLDOUT_EVERY == 0 else "train"
            handle.write(json.dumps(payload) + "\n")

    rows = sum(tune.rows for tune in tunes)
    holdout = sum(1 for index in range(len(tunes)) if index % HOLDOUT_EVERY == 0)
    print(f"chorales considered: {len(scores)}")
    print(f"extracted:           {len(tunes)}   rows: {rows}")
    print(f"train / holdout:     {len(tunes) - holdout} / {holdout}")
    if rejected:
        print("rejected:")
        for reason, count in rejected.most_common():
            print(f"  {count:>4}  {reason}")
    if tunes:
        print()
        print(f"sample: {tunes[0].title}  ({tunes[0].mode}, {tunes[0].metre})")
        print(f"  {describe(tunes[0])}")
    print(f"\nwrote {arguments.output}")


if __name__ == "__main__":
    main()
