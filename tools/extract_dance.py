#!/usr/bin/env python3
"""Reduce public-domain dance tunes to the EXP-009 player's row grid.

Ryan's Mammoth Collection (1883), O'Neill's Music of Ireland (1903) and Aird's
Selection (1780s) are bundled with music21 and are unambiguously public domain
by age. They are melody only, so the chord token is inferred rather than read.
See src/reference/chord_inference.py for why that is acceptable here and would
not have been for chorales.

A row is a sixteenth note rather than the eighth used for chorales. Reels and
hornpipes are notated in running sixteenths; at eighth resolution half the tune
disappears.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from chord_inference import WindowNote, infer_progression
from melody_tokens import (
    HOLD,
    METRES,
    REST,
    Tune,
    chord_token,
    describe,
    pitch_token,
    rows_per_bar,
)

ROW_QUARTER_LENGTH = 0.25  # a sixteenth note
DEFAULT_OUTPUT = ROOT / "experiments" / "data" / "EXP-010-dance.jsonl"
HOLDOUT_EVERY = 6
COLLECTIONS = ("ryansMammoth", "oneills1850", "airdsAirs", "miscFolk")


def tonic_below(tonic_pitch_class: int, lowest_midi: int) -> int:
    candidate = tonic_pitch_class
    while candidate + 12 <= lowest_midi:
        candidate += 12
    while candidate > lowest_midi:
        candidate -= 12
    return candidate


def extract(score, source: str):
    key = score.analyze("key")
    if key.mode not in ("major", "minor"):
        return None, f"unsupported mode {key.mode}"

    signatures = list(score.recurse().getElementsByClass("TimeSignature"))
    if not signatures:
        return None, "no time signature"
    metre = signatures[0].ratioString
    if metre not in METRES:
        return None, f"unsupported metre {metre}"

    flat = score.flatten().notesAndRests.stream()
    notes = [element for element in flat if element.isNote]
    if len(notes) < 16:
        return None, "too short"

    lowest = min(note.pitch.midi for note in notes)
    tonic_midi = tonic_below(key.tonic.pitchClass, lowest)
    bar_rows = rows_per_bar(metre, ROW_QUARTER_LENGTH)

    spans: list[tuple[int, int, int, int]] = []
    for note in notes:
        start = round(float(note.offset) / ROW_QUARTER_LENGTH)
        length = max(1, round(float(note.quarterLength) / ROW_QUARTER_LENGTH))
        token = pitch_token(note.pitch.midi - tonic_midi)
        if token is None:
            return None, "melody leaves the pitch range"
        relative = (note.pitch.midi - tonic_midi) % 12
        spans.append((start, length, token, relative))

    row_count = max(start + length for start, length, _, _ in spans)
    if row_count > 4096:
        return None, "unreasonably long"

    melody = [REST] * row_count
    for start, length, token, _ in spans:
        melody[start] = token
        for offset in range(start + 1, min(start + length, row_count)):
            melody[offset] = HOLD

    # Group notes into bars, then infer one chord per bar.
    bar_count = -(-row_count // bar_rows)
    bars: list[list[WindowNote]] = [[] for _ in range(bar_count)]
    for start, length, _, relative in spans:
        bar = start // bar_rows
        if bar < bar_count:
            bars[bar].append(
                WindowNote(
                    pitch_class=relative,
                    duration=float(length),
                    position=start % bar_rows,
                )
            )

    progression = infer_progression(bars, key.mode, bar_rows)
    chords = [chord_token(progression[row // bar_rows] + 1) for row in range(row_count)]
    beats = [row % bar_rows for row in range(row_count)]

    return (
        Tune(
            source=source,
            title=str(score.metadata.title or source),
            mode=key.mode,
            metre=metre,
            tonic=key.tonic.name,
            melody=tuple(melody),
            chords=tuple(chords),
            beats=tuple(beats),
        ),
        None,
    )


def iter_scores(collection: str, limit: int, unreadable: Counter):
    """Yield every score in a collection, counting files that will not parse.

    A file that fails to parse must not stop the run, but it must not vanish
    either: the count is reported alongside the rejections.
    """
    from music21 import corpus

    paths = sorted(corpus.getComposer(collection))
    count = 0
    for path in paths:
        try:
            parsed = corpus.parse(path)
        except Exception as error:  # noqa: BLE001 - recorded, then skipped
            unreadable[type(error).__name__] += 1
            continue
        scores = getattr(parsed, "scores", None)
        for score in list(scores) if scores else [parsed]:
            yield score
            count += 1
            if limit and count >= limit:
                return


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--collections", type=str, default="ryansMammoth")
    parser.add_argument("--limit", type=int, default=0, help="0 means all")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    tunes: list[Tune] = []
    rejected: Counter[str] = Counter()
    unreadable: Counter[str] = Counter()

    for collection in arguments.collections.split(","):
        for index, score in enumerate(
            iter_scores(collection, arguments.limit, unreadable)
        ):
            source = f"{collection}/{index}"
            try:
                tune, reason = extract(score, source)
            except Exception as error:  # noqa: BLE001 - record and continue
                tune, reason = None, type(error).__name__
            if tune is None:
                rejected[reason or "unknown"] += 1
                continue
            tunes.append(tune)

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("w", encoding="utf-8") as handle:
        for index, tune in enumerate(tunes):
            payload = tune.to_json()
            payload["split"] = "holdout" if index % HOLDOUT_EVERY == 0 else "train"
            payload["chords_inferred"] = True
            handle.write(json.dumps(payload) + "\n")

    rows = sum(tune.rows for tune in tunes)
    holdout = sum(1 for index in range(len(tunes)) if index % HOLDOUT_EVERY == 0)
    print(f"extracted: {len(tunes)} tunes, {rows} rows")
    print(f"train / holdout: {len(tunes) - holdout} / {holdout}")
    if unreadable:
        print("files that would not parse:")
        for reason, count in unreadable.most_common(4):
            print(f"  {count:>5}  {reason}")
    if rejected:
        print("rejected:")
        for reason, count in rejected.most_common(8):
            print(f"  {count:>5}  {reason}")
    if tunes:
        print()
        print(f"sample: {tunes[0].title} ({tunes[0].mode}, {tunes[0].metre})")
        print(f"  {describe(tunes[0], limit=24)}")
    print(f"\nwrote {arguments.output}")


if __name__ == "__main__":
    main()
