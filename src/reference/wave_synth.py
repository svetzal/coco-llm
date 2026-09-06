"""Wavetable voices for the CoCo synthesizer: the reference for EXP-017.

EXP-009's player makes each tone voice one bit: bit 15 of a phase
accumulator, masked against a volume. This player keeps the accumulator
and replaces the mask with a table: the accumulator's high byte indexes a
256-entry page of a waveform, and the voice's volume selects which of
sixteen pages. On the 6809 the lookup costs the same as the mask did, so
the sample rate does not move; only the shape of the wave does.

Everything here is integer and mirrors the assembly step for step, so the
table the CoCo reads and the table this model reads are the same bytes.
The noise voice is unchanged from EXP-009.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
from coco_synth import (
    MAX_VOLUME,
    NOISE_VOICE,
    NOTE_HOLD,
    NOTE_OFF,
    PHASE_BITS,
    VOICE_COUNT,
    Cell,
    Tune,
    Voice,
    note_increment,
)
from numpy.typing import NDArray

PAGE_SAMPLES = 256
PAGES = MAX_VOLUME + 1

# A shape maps a phase position, 0 to 255, onto 0.0 to 1.0. Unipolar, like
# the one-bit square it replaces: the DAC has no negative half.
SHAPES: dict[str, Callable[[int], float]] = {
    "square": lambda p: 1.0 if p >= 128 else 0.0,
    "triangle": lambda p: p / 128 if p < 128 else (256 - p) / 128,
    "sine": lambda p: (1.0 - math.cos(2.0 * math.pi * p / 256)) / 2.0,
}


def wave_table(shape: str) -> list[list[int]]:
    """Sixteen pages of 256 samples: table[volume][phase_high_byte].

    Values are DAC units, 0 to 15 per voice, so four voices at full volume
    sum to 60 and fit the 6-bit DAC. The `square` shape reproduces
    EXP-009's masked bit exactly: the page holds the volume wherever
    bit 7 of the high byte, which is bit 15 of the phase, is set.
    """
    curve = SHAPES[shape]
    return [
        [int(curve(position) * volume + 0.5) for position in range(PAGE_SAMPLES)]
        for volume in range(PAGES)
    ]


@dataclass
class WaveSynth:
    """Bit-exact model of the wavetable player's state and per-sample work."""

    sample_rate: int
    table: list[list[int]]
    voices: list[Voice] = field(
        default_factory=lambda: [Voice() for _ in range(VOICE_COUNT)]
    )

    def __post_init__(self) -> None:
        self.voices[NOISE_VOICE].noise = True

    def apply_cell(self, number: int, cell: Cell) -> None:
        voice = self.voices[number]
        if cell.note == NOTE_HOLD:
            return
        if cell.note == NOTE_OFF:
            voice.volume = 0
            return
        if number != NOISE_VOICE:
            voice.increment = note_increment(cell.note, self.sample_rate)
            voice.phase = 0
        voice.volume = min(MAX_VOLUME, cell.volume)
        voice.decay = cell.decay

    def apply_decay(self, number: int) -> None:
        voice = self.voices[number]
        if voice.decay and voice.volume:
            voice.volume = max(0, voice.volume - voice.decay)

    def sample(self) -> int:
        total = 0
        for voice in self.voices:
            bit = voice.step()
            if voice.noise:
                total += voice.volume if bit else 0
            else:
                total += self.table[voice.volume][voice.phase >> (PHASE_BITS - 8)]
        return total


def render(tune: Tune, *, sample_rate: int, shape: str) -> NDArray[np.int64]:
    """Render one pass of a tune to 6-bit DAC values, on the player's timeline.

    The player applies a row's four cells one per sample, and a tick's four
    decays one per sample, so that no pause between samples is longer than a
    sample. This follows that exactly: one sample on the old state, then one
    after each cell or decay, then the rest of the tick. Each pass opens with
    the single silent sample the player emits before it fetches row 0.
    """
    synth = WaveSynth(sample_rate=sample_rate, table=wave_table(shape))
    samples_per_tick = max(1, round(sample_rate / tune.tick_hz))
    if samples_per_tick < VOICE_COUNT + 1:
        raise ValueError("a tick must hold at least five samples")
    output: list[int] = [synth.sample()]

    for row in tune.rows:
        for tick in range(tune.ticks_per_row):
            output.append(synth.sample())
            for number in range(VOICE_COUNT):
                if tick == 0:
                    synth.apply_cell(number, row[number])
                else:
                    synth.apply_decay(number)
                output.append(synth.sample())
            for _ in range(samples_per_tick - VOICE_COUNT - 1):
                output.append(synth.sample())

    return np.asarray(output, dtype=np.int64)
