"""Reference implementation of the CoCo 1 four-voice software synthesizer.

This models exactly what the 6809 player will do, so the Mac can render a tune
to a WAV file and the assembly can be checked against the same sample stream.

The technique is the classic one for a machine with a single 6-bit DAC and no
sound chip: every voice is a one-bit source, and the mix is a table lookup.

Voices 0 to 2 own a 16-bit phase accumulator and a 16-bit increment. Adding
the increment each sample and taking bit 15 gives a square wave whose
frequency is set by the increment alone, with the full precision of a 16-bit
divisor.

Voice 3 is a dedicated noise channel, like the noise generator on a period
sound chip. It has no phase accumulator; a linear-feedback shift register is
clocked once per sample and its low bit is the output.

That split exists for timing, not for taste. A software DAC has no timer: the
sample rate *is* the loop's cycle count, so the loop must cost the same every
pass. An earlier design clocked the LFSR only when a phase accumulator
wrapped, which made the loop branch three ways and swing the sample period by
24%. That is frequency modulation, and it sounds like it. Every branch in the
sample path is now gone.

Because every voice contributes either zero or its own amplitude, the sum of
four voices takes only sixteen possible values. Those sixteen sums are
precomputed into a table whenever a volume changes, which happens on row
boundaries rather than per sample. The per-sample cost is then four phase
adds, four bit extractions, one table lookup, and one store to the DAC. No
multiplication, no division, and no per-sample addition of amplitudes.

Amplitudes are capped so four voices at full volume sum to 60, inside the
6-bit DAC range of 0 to 63, so the table never needs to clamp or scale.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

VOICE_COUNT = 4
MAX_VOLUME = 15
DAC_MAX = 63
PHASE_BITS = 16
PHASE_MASK = (1 << PHASE_BITS) - 1

# x^16 + x^14 + x^13 + x^11 + 1, the usual maximal-length 16-bit right-shift
# LFSR. On the 6809 this is a shift and a conditional EOR of two bytes.
LFSR_TAPS = 0xB400
LFSR_SEED = 0xACE1

# Voice 3 is the noise channel. Voices 0 to 2 are always square.
NOISE_VOICE = 3

# MIDI note 69 is A4 at 440 Hz.
CONCERT_A = 440.0
CONCERT_A_NOTE = 69

NOTE_HOLD = -1
NOTE_OFF = -2


def note_frequency(note: int) -> float:
    return CONCERT_A * (2.0 ** ((note - CONCERT_A_NOTE) / 12.0))


def note_increment(note: int, sample_rate: int) -> int:
    """Phase increment for a note, as the 6809 lookup table will store it."""
    increment = round(note_frequency(note) * (1 << PHASE_BITS) / sample_rate)
    return max(1, min(PHASE_MASK, increment))


def build_increment_table(
    lowest: int, highest: int, sample_rate: int
) -> dict[int, int]:
    return {
        note: note_increment(note, sample_rate) for note in range(lowest, highest + 1)
    }


def build_mix_table(volumes: Sequence[int]) -> NDArray[np.int64]:
    """The sixteen possible sums of four one-bit voices.

    Index bit v is set when voice v is currently high. Rebuilt only when a
    volume changes, so the per-sample path is a single indexed load.
    """
    table = np.zeros(1 << VOICE_COUNT, dtype=np.int64)
    for index in range(1 << VOICE_COUNT):
        total = 0
        for voice in range(VOICE_COUNT):
            if index & (1 << voice):
                total += volumes[voice]
        table[index] = min(DAC_MAX, total)
    return table


@dataclass
class Voice:
    increment: int = 0
    phase: int = 0
    volume: int = 0
    decay: int = 0
    noise: bool = False
    lfsr: int = LFSR_SEED
    bit: int = 0

    def step(self) -> int:
        """Advance one sample and return this voice's current one-bit output.

        Both paths are branch-free on the 6809 and cost a fixed number of
        cycles, so the sample period never varies.
        """
        if self.noise:
            carry = self.lfsr & 1
            self.lfsr >>= 1
            if carry:
                self.lfsr ^= LFSR_TAPS
            self.bit = self.lfsr & 1
            return self.bit

        self.phase = (self.phase + self.increment) & PHASE_MASK
        self.bit = (self.phase >> (PHASE_BITS - 1)) & 1
        return self.bit


@dataclass(frozen=True)
class Cell:
    """One channel's instruction on one row.

    `note` is a MIDI note number, `NOTE_HOLD` to leave the voice alone, or
    `NOTE_OFF` to silence it. `decay` subtracts from volume once per tick,
    which is what gives percussion its shape without an envelope generator.

    On voice 3 the note only retriggers the channel; its pitch is ignored,
    because the noise generator has no phase accumulator.
    """

    note: int = NOTE_HOLD
    volume: int = MAX_VOLUME
    decay: int = 0


@dataclass(frozen=True)
class Tune:
    name: str
    rows: tuple[tuple[Cell, ...], ...]
    ticks_per_row: int = 6
    tick_hz: int = 50

    @property
    def seconds(self) -> float:
        return len(self.rows) * self.ticks_per_row / self.tick_hz


@dataclass
class Synth:
    """Bit-exact model of the 6809 player's state and per-sample work."""

    sample_rate: int = 7300
    voices: list[Voice] = field(default_factory=lambda: [Voice() for _ in range(4)])
    mix_table: NDArray[np.int64] = field(
        default_factory=lambda: build_mix_table([0] * 4)
    )

    def __post_init__(self) -> None:
        self.voices[NOISE_VOICE].noise = True

    def apply_row(self, row: Sequence[Cell]) -> None:
        for number, (voice, cell) in enumerate(zip(self.voices, row, strict=True)):
            if cell.note == NOTE_HOLD:
                continue
            if cell.note == NOTE_OFF:
                voice.volume = 0
                continue
            if number != NOISE_VOICE:
                voice.increment = note_increment(cell.note, self.sample_rate)
                voice.phase = 0
            voice.volume = min(MAX_VOLUME, cell.volume)
            voice.decay = cell.decay
        self.refresh_mix_table()

    def apply_tick(self) -> None:
        changed = False
        for voice in self.voices:
            if voice.decay and voice.volume:
                voice.volume = max(0, voice.volume - voice.decay)
                changed = True
        if changed:
            self.refresh_mix_table()

    def refresh_mix_table(self) -> None:
        self.mix_table = build_mix_table([voice.volume for voice in self.voices])

    def sample(self) -> int:
        index = 0
        for number, voice in enumerate(self.voices):
            index |= voice.step() << number
        return int(self.mix_table[index])


def render(tune: Tune, *, sample_rate: int = 7300) -> NDArray[np.int64]:
    """Render a tune to a stream of 6-bit DAC values, 0 to 63."""
    synth = Synth(sample_rate=sample_rate)
    samples_per_tick = max(1, round(sample_rate / tune.tick_hz))
    output: list[int] = []

    for row in tune.rows:
        synth.apply_row(row)
        for tick in range(tune.ticks_per_row):
            if tick:
                synth.apply_tick()
            for _ in range(samples_per_tick):
                output.append(synth.sample())

    return np.asarray(output, dtype=np.int64)


def demo_tune() -> Tune:
    """A short A-minor riff exercising tone, bass, arpeggio, and percussion.

    Voice 0 is bass, voice 1 melody, voice 2 an arpeggio that drops to a low
    kick on each downbeat, and voice 3 the noise channel. The kick lives on a
    tone voice because voice 3 has no phase accumulator and cannot be pitched.
    Everything percussive is shaped by per-tick decay alone.
    """
    bass_line = [45, 45, 48, 48, 50, 50, 52, 52]
    melody = [69, 72, 76, 74, 72, 69, 67, 69, 72, 76, 79, 76, 74, 72, 69, 69]
    arpeggio = [57, 60, 64, 60]

    kick = Cell(note=24, volume=15, decay=4)
    snare = Cell(note=60, volume=11, decay=2)
    hat = Cell(note=60, volume=4, decay=4)
    silent = Cell(note=NOTE_HOLD)

    rows: list[tuple[Cell, ...]] = []
    for index in range(32):
        bass = (
            Cell(note=bass_line[(index // 4) % len(bass_line)], volume=12)
            if index % 4 == 0
            else silent
        )
        lead = (
            Cell(note=melody[(index // 2) % len(melody)], volume=13, decay=1)
            if index % 2 == 0
            else silent
        )
        harmony = (
            kick
            if index % 4 == 0
            else Cell(note=arpeggio[index % len(arpeggio)], volume=6, decay=1)
        )

        if index % 4 == 2:
            drum = snare
        elif index % 2 == 1:
            drum = hat
        else:
            drum = silent

        rows.append((bass, lead, harmony, drum))

    return Tune(name="EXP-009 demo", rows=tuple(rows), ticks_per_row=6, tick_hz=50)


def to_waveform(dac_values: NDArray[np.int64]) -> NDArray[np.int16]:
    """Convert 6-bit DAC values to signed 16-bit PCM for a WAV file.

    This is a listening aid, not part of the model of the machine. The DAC
    values themselves are what the CoCo emits and what the assembly must
    reproduce.

    The offset removed is the signal's own mean rather than the midpoint of the
    DAC range. Real tunes sit well below mid-scale, because most of the time
    most voices are low, so centring on the nominal midpoint would leave a
    large DC step and throw away headroom.
    """
    centred = dac_values.astype(np.float64) - float(np.mean(dac_values))
    peak = max(1.0, float(np.max(np.abs(centred))))
    return np.asarray(centred / peak * 0.6 * 32767, dtype=np.int16)
