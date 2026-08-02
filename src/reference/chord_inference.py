"""Infer a chord per bar from an unharmonised melody.

The chorale corpus states its harmony: the alto, tenor and bass say what the
chord is. The public-domain dance collections do not — Ryan's Mammoth,
O'Neill's and Aird's are melody only. Since the EXP-010 ablation showed the
chord token carries nearly the whole of the model's advantage, a chordless
corpus is unusable, so the chord has to be recovered from the tune.

This is defensible for dance music in a way it would not have been for
chorales. Reels, jigs and hornpipes sit on I, IV and V with chord tones on the
strong beats; the harmony is close to determined by the melody. It would be a
poor idea for Bach, whose whole interest is harmony the melody does not imply.

What is lost is the claim that the chord is ground truth. It becomes a derived
feature, and must be described that way. The comparison in Phase A stays fair
regardless, because the model and the table baselines receive the same derived
feature — inference is not a thumb on the model's scale.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

MAJOR_STEPS = (0, 2, 4, 5, 7, 9, 11)
MINOR_STEPS = (0, 2, 3, 5, 7, 8, 10)

# Dance harmony is overwhelmingly tonic, subdominant and dominant. This breaks
# ties toward the chords the idiom actually uses rather than toward whichever
# triad happens to share a passing note.
DEGREE_PRIOR = (1.00, 0.72, 0.68, 0.92, 0.96, 0.78, 0.62)

# A note landing on the downbeat says far more about the harmony than one
# passing through the middle of the bar.
DOWNBEAT_WEIGHT = 2.5
STRONG_WEIGHT = 1.5


def scale_steps(mode: str) -> tuple[int, ...]:
    return MAJOR_STEPS if mode == "major" else MINOR_STEPS


def triad_pitch_classes(degree: int, steps: Sequence[int]) -> set[int]:
    """Pitch classes of the diatonic triad built on this scale degree."""
    return {steps[(degree + offset) % 7] for offset in (0, 2, 4)}


@dataclass(frozen=True)
class WindowNote:
    """One note inside a bar: pitch class above the tonic, and its weight."""

    pitch_class: int
    duration: float
    position: int  # rows from the start of the bar

    def weight(self, bar_rows: int) -> float:
        if self.position == 0:
            emphasis = DOWNBEAT_WEIGHT
        elif bar_rows and self.position == bar_rows // 2:
            emphasis = STRONG_WEIGHT
        else:
            emphasis = 1.0
        return self.duration * emphasis


def infer_chord(
    notes: Sequence[WindowNote], mode: str, bar_rows: int, previous: int | None = None
) -> int:
    """Best diatonic triad for one bar, as a zero-based scale degree.

    Scores each triad by how much weighted note duration it explains, applies
    an idiom prior, and mildly prefers holding the previous chord so that a
    single passing note does not cause a spurious change.
    """
    steps = scale_steps(mode)
    if not notes:
        return previous if previous is not None else 0

    best_degree, best_score = 0, float("-inf")
    for degree in range(7):
        tones = triad_pitch_classes(degree, steps)
        explained = sum(
            note.weight(bar_rows) for note in notes if note.pitch_class in tones
        )
        score = explained * DEGREE_PRIOR[degree]
        if previous is not None and degree == previous:
            score *= 1.06
        if score > best_score:
            best_degree, best_score = degree, score

    return best_degree


def infer_progression(
    bars: Sequence[Sequence[WindowNote]], mode: str, bar_rows: int
) -> list[int]:
    progression: list[int] = []
    previous: int | None = None
    for bar in bars:
        chord = infer_chord(bar, mode, bar_rows, previous)
        progression.append(chord)
        previous = chord
    return progression
