"""Generate a melody and arrange it for the EXP-009 player.

Two separable jobs, kept separate on purpose.

Generation samples melody rows from the model, conditioned on a chord and
metric position it is given rather than one it invents. Sampling is by
temperature, not argmax: a model that always takes its most probable row scores
well on cross-entropy and produces something that circles a few notes and dies.

Arrangement turns those rows into the player's four voices. It supplies the
bass, the arpeggio and the drums from the chord progression, and it chooses the
tempo. Nothing about pacing or energy comes from the corpus — that is the point
of the split. The same generated pitches can be performed stately or driven.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from coco_synth import NOTE_HOLD, NOTE_OFF, Cell
from coco_synth import Tune as PlayerTune
from melody_lm import PAD, MelodyConfig, MelodyModel, context_prefix
from melody_tokens import HOLD, REST, Tune

MAJOR_STEPS = (0, 2, 4, 5, 7, 9, 11)
MINOR_STEPS = (0, 2, 3, 5, 7, 8, 10)

# Where the generated tonic sits on the player's keyboard.
MELODY_TONIC = 60
BASS_TONIC = MELODY_TONIC - 24
ARPEGGIO_TONIC = MELODY_TONIC - 12


def scale_steps(mode: str) -> tuple[int, ...]:
    return MAJOR_STEPS if mode == "major" else MINOR_STEPS


def generate(
    model: MelodyModel,
    config: MelodyConfig,
    source: Tune,
    *,
    seed_rows: int,
    temperature: float,
    rng: np.random.Generator,
    diatonic_only: bool = False,
) -> list[int]:
    """Continue `source`'s opening rows over its own chords and metre.

    The first `seed_rows` are copied verbatim; everything after is sampled.
    That is the demonstration exactly: a person supplies an opening bar and the
    machine continues it.
    """
    allowed = None
    if diatonic_only:
        steps = set(scale_steps(source.mode))
        allowed = np.array(
            [
                token in (HOLD, REST) or (token % 12) in steps
                for token in range(model.biases.size)
            ]
        )

    history = [PAD] * config.history
    rows: list[int] = []

    for row in range(source.rows):
        if row < seed_rows:
            token = source.melody[row]
        else:
            prefix = context_prefix(source, row, config.features)
            context = np.asarray([[*prefix, *history]], dtype=np.int64)
            logits = model.logits(context)[0]
            if allowed is not None:
                logits = np.where(allowed, logits, -np.inf)
            scaled = logits / max(1e-6, temperature)
            scaled -= scaled.max()
            weights = np.exp(scaled)
            token = int(rng.choice(len(weights), p=weights / weights.sum()))

        rows.append(token)
        history = history[1:] + [token]

    return rows


def _drum(beat: int, bar_rows: int) -> Cell:
    """Kick on the downbeat, snare on the backbeat, hats between."""
    if beat == 0:
        return Cell(note=60, volume=13, decay=4)
    if beat == bar_rows // 2:
        return Cell(note=60, volume=10, decay=3)
    if beat % 2 == 0:
        return Cell(note=60, volume=3, decay=5)
    return Cell(note=NOTE_HOLD)


def arrange(
    melody: Sequence[int],
    source: Tune,
    *,
    ticks_per_row: int,
    bar_rows: int,
    drums: bool = True,
) -> PlayerTune:
    """Lay a generated melody onto the player's four voices."""
    steps = scale_steps(source.mode)
    rows: list[tuple[Cell, ...]] = []
    last_chord: int | None = None

    for row, token in enumerate(melody):
        chord = source.chords[row]
        beat = source.beats[row]
        root = steps[chord]

        if token == HOLD:
            lead = Cell(note=NOTE_HOLD)
        elif token == REST:
            lead = Cell(note=NOTE_OFF)
        else:
            lead = Cell(note=MELODY_TONIC + token, volume=13, decay=0)

        if chord != last_chord:
            bass = Cell(note=BASS_TONIC + root, volume=12, decay=0)
            last_chord = chord
        else:
            bass = Cell(note=NOTE_HOLD)

        # Arpeggio walks the triad, so the harmony moves even when the melody
        # holds. Thirds and fifths come from the mode, not from the corpus.
        tone = (0, 2, 4)[row % 3]
        pitch = ARPEGGIO_TONIC + steps[(chord + tone) % 7] + (12 if tone else 0)
        harmony = Cell(note=pitch, volume=5, decay=1)

        percussion = _drum(beat, bar_rows) if drums else Cell(note=NOTE_OFF)
        rows.append((bass, lead, harmony, percussion))

    return PlayerTune(
        name=f"generated from {source.title}",
        rows=tuple(rows),
        ticks_per_row=ticks_per_row,
        tick_hz=50,
    )
