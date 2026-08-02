"""Token alphabet for EXP-010 melody continuation.

Pure functions only. The music21 dependency lives in tools/extract_chorales.py
so that the token definitions can be tested without it, and so the CoCo-facing
side never acquires a music-analysis library.

A row is the player's row: one cell, one token. Pitch is expressed in
semitones above the tonic rather than as an absolute note, so every key
collapses onto one alphabet.

That collapsing is the point, and it is worth being precise about what it
buys. It does not shrink the vocabulary much: chorale sopranos need about
twenty-five relative semitones, and absolute pitches across all keys would
need a similar spread. What it buys is data density — a phrase learned in
G minor is the same sequence of tokens in D minor, so every tune reinforces
every other rather than occupying its own corner of the alphabet.

Chromatic degrees are used rather than the seven diatonic ones because 3.7% of
chorale melody notes fall outside the scale, and in minor those are the raised
sixth and seventh. The raised seventh is the leading tone; discarding it would
remove the thing that makes a cadence.
"""

from __future__ import annotations

from dataclasses import dataclass

# One row is an eighth note. Chorale melodies are mostly quarters and eighths,
# so this resolves every note without wasting rows on ties.
ROW_QUARTER_LENGTH = 0.5

# Semitones above the tonic. The tonic is taken in the octave at or below the
# melody's lowest note, so a relative pitch is never negative.
#
# The ceiling is measured, not assumed. A melody spanning an octave can still
# reach 24 semitones above the tonic, because the tonic may sit up to eleven
# semitones below the lowest note it uses. An earlier ceiling of 17 was set
# from the melodic span alone and rejected 15% of the chorale corpus.
#
# Fiddle tunes reach higher than chorale melodies: measured over Ryan's
# Mammoth, 99.9% of notes fall within 31 semitones of the tonic and the
# maximum is 33. A ceiling of 24 rejected nearly half of those tunes, because
# one note over the line discards the whole tune.
LOWEST_RELATIVE = 0
HIGHEST_RELATIVE = 31
PITCH_COUNT = HIGHEST_RELATIVE - LOWEST_RELATIVE + 1

HOLD = PITCH_COUNT
REST = PITCH_COUNT + 1
MELODY_TOKENS = PITCH_COUNT + 2

MODES = ("major", "minor")
# Chorale metres first, then the dance metres. Appending keeps existing token
# indices stable, so the chorale corpus does not need re-extracting.
METRES = ("4/4", "3/4", "3/2", "2/4", "2/2", "6/8", "9/8", "12/8", "3/8")
CHORDS = (1, 2, 3, 4, 5, 6, 7)
MAX_BEATS = 8

DEGREE_NAMES = (
    "1",
    "b2",
    "2",
    "b3",
    "3",
    "4",
    "#4",
    "5",
    "b6",
    "6",
    "b7",
    "7",
)


def pitch_token(relative_semitones: int) -> int | None:
    """Token for a pitch this many semitones above the tonic, or None."""
    if not LOWEST_RELATIVE <= relative_semitones <= HIGHEST_RELATIVE:
        return None
    return relative_semitones - LOWEST_RELATIVE


def token_name(token: int) -> str:
    if token == HOLD:
        return "HOLD"
    if token == REST:
        return "REST"
    relative = token + LOWEST_RELATIVE
    octave = relative // 12
    name = DEGREE_NAMES[relative % 12]
    return name if octave == 0 else f"{name}+{octave}"


def mode_token(mode: str) -> int:
    return MODES.index(mode)


def metre_token(ratio: str) -> int | None:
    return METRES.index(ratio) if ratio in METRES else None


def chord_token(scale_degree: int) -> int:
    """Chord roots are scale degrees 1..7, stored zero-based."""
    if not 1 <= scale_degree <= 7:
        raise ValueError(f"chord degree {scale_degree} outside 1..7")
    return scale_degree - 1


def rows_per_bar(ratio: str, row_quarter_length: float = ROW_QUARTER_LENGTH) -> int:
    """Rows in one bar of this metre, at the given row resolution.

    Chorales are encoded a row to the eighth note. Dance tunes are notated in
    running sixteenths, so a reel needs a row to the sixteenth or half its
    notes are lost.
    """
    numerator, denominator = (int(part) for part in ratio.split("/"))
    quarters = numerator * 4 / denominator
    return max(1, round(quarters / row_quarter_length))


@dataclass(frozen=True)
class Tune:
    """One chorale, reduced to the player's row grid."""

    source: str
    title: str
    mode: str
    metre: str
    tonic: str
    melody: tuple[int, ...]
    chords: tuple[int, ...]
    beats: tuple[int, ...]

    def __post_init__(self) -> None:
        if not len(self.melody) == len(self.chords) == len(self.beats):
            raise ValueError(f"{self.source}: row streams have different lengths")

    @property
    def rows(self) -> int:
        return len(self.melody)

    def to_json(self) -> dict:
        return {
            "source": self.source,
            "title": self.title,
            "mode": self.mode,
            "metre": self.metre,
            "tonic": self.tonic,
            "melody": list(self.melody),
            "chords": list(self.chords),
            "beats": list(self.beats),
        }

    @classmethod
    def from_json(cls, payload: dict) -> Tune:
        return cls(
            source=str(payload["source"]),
            title=str(payload["title"]),
            mode=str(payload["mode"]),
            metre=str(payload["metre"]),
            tonic=str(payload["tonic"]),
            melody=tuple(int(value) for value in payload["melody"]),
            chords=tuple(int(value) for value in payload["chords"]),
            beats=tuple(int(value) for value in payload["beats"]),
        )


def describe(tune: Tune, limit: int = 16) -> str:
    return " ".join(token_name(token) for token in tune.melody[:limit])
