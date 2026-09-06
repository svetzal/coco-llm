"""The steady sample clock: the reference for EXP-018.

EXP-009's player does its row and tick work between samples, and each
piece of that work stretches the sample it borrows by most of a period.
At a row change that is five stretched samples in a row, 8.33 times a
second in the demo tune, and a sustained note's phase slips by about four
periods every time. That is the warble heard on the CoCo 3.

This player has no row or tick work at all. The tune is compiled ahead of
time into a stream of events, each one byte written into the player's
direct page after a wait of so many samples, and the sample loop applies
at most one event per sample through a path padded to cost exactly what
the idle path costs. Every sample then costs the same number of cycles,
whatever the tune is doing, and the sample clock never moves.

The state the events write is EXP-009's: phase accumulators, increments
and pre-shifted volumes. Decay is computed here, not on the CoCo, so the
stream carries the resulting volumes. The sample arithmetic is EXP-009's,
byte for byte, which is what makes the two players comparable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from coco_synth import (
    LFSR_SEED,
    LFSR_TAPS,
    MAX_VOLUME,
    NOISE_VOICE,
    NOTE_HOLD,
    NOTE_OFF,
    VOICE_COUNT,
    Tune,
    note_increment,
)
from numpy.typing import NDArray

# The direct page of steady_player.asm, as offsets from $2000. The parity
# test checks the assembled symbols against these.
PHASES = 0x00
INCRS = 0x08
SCALED = 0x10
DAC_ACC = 0x14
LFSR = 0x15
TICK_SAMPLES = 0x17
FINISHED = 0x18
SCRATCH = 0x19
STATE_BYTES = 0x14  # phases, increments and volumes: cleared at reset
PAGE_BYTES = 0x1A

MAX_WAIT = 255
WRITES_PER_CELL = 5


@dataclass(frozen=True)
class Event:
    """One byte written to the direct page after `wait` more samples."""

    wait: int
    offset: int
    value: int


def compile_events(tune: Tune, sample_rate: int) -> list[Event]:
    """Turn a tune into the event stream the player replays.

    A tick is `samples_per_tick` samples exactly. Its state changes are
    applied one per sample starting after the tick's first sample, so
    the first sample of every tick is on the previous state, as in the
    other players. A note is five writes (increment, phase reset, volume),
    so a tick must be long enough to hold five per voice.
    """
    samples_per_tick = round(sample_rate / tune.tick_hz)
    if samples_per_tick < 1 + WRITES_PER_CELL * VOICE_COUNT:
        raise ValueError(f"{samples_per_tick} samples per tick cannot hold a row")

    volumes = [0] * VOICE_COUNT
    decays = [0] * VOICE_COUNT
    timed: list[tuple[int, int, int]] = []

    for row_number, row in enumerate(tune.rows):
        if len(row) != VOICE_COUNT:
            raise ValueError(f"row {row_number} has {len(row)} cells")
        for tick in range(tune.ticks_per_row):
            start = (row_number * tune.ticks_per_row + tick) * samples_per_tick
            writes: list[tuple[int, int]] = []
            for number in range(VOICE_COUNT):
                if tick == 0:
                    cell = row[number]
                    if cell.note == NOTE_HOLD:
                        continue
                    if cell.note == NOTE_OFF:
                        volumes[number] = 0
                        writes.append((SCALED + number, 0))
                        continue
                    if number != NOISE_VOICE:
                        increment = note_increment(cell.note, sample_rate)
                        writes.append((INCRS + 2 * number, increment >> 8))
                        writes.append((INCRS + 2 * number + 1, increment & 0xFF))
                        writes.append((PHASES + 2 * number, 0))
                        writes.append((PHASES + 2 * number + 1, 0))
                    volumes[number] = min(MAX_VOLUME, cell.volume)
                    decays[number] = cell.decay
                    writes.append((SCALED + number, volumes[number] << 2))
                elif decays[number] and volumes[number]:
                    volumes[number] = max(0, volumes[number] - decays[number])
                    writes.append((SCALED + number, volumes[number] << 2))
            for index, (offset, value) in enumerate(writes):
                timed.append((start + 1 + index, offset, value))

    total = len(tune.rows) * tune.ticks_per_row * samples_per_tick
    timed.append((total, FINISHED, 1))

    events: list[Event] = []
    previous = 0
    for at, offset, value in timed:
        wait = at - previous
        while wait > MAX_WAIT:
            events.append(Event(MAX_WAIT, SCRATCH, 0))
            wait -= MAX_WAIT
        events.append(Event(wait, offset, value))
        previous = at
    return events


def stream_bytes(events: list[Event]) -> bytes:
    """The stream as the player reads it: a wait, then offset, value, wait,
    offset, value, ... and a spare byte after the last event, which the
    player reads as a wait it never uses."""
    out = bytearray()
    for event in events:
        out += bytes((event.wait, event.offset, event.value))
    out.append(0)
    return bytes(out)


def render(tune: Tune, *, sample_rate: int) -> NDArray[np.int64]:
    """One pass of the tune, exactly as the player produces it."""
    events = compile_events(tune, sample_rate)
    state = bytearray(PAGE_BYTES)
    lfsr = LFSR_SEED
    output: list[int] = []

    pending = iter(events)
    event = next(pending)
    wait = event.wait
    while True:
        dac = 0
        carry = lfsr & 1
        lfsr >>= 1
        if carry:
            lfsr ^= LFSR_TAPS
        if lfsr & 1:
            dac += state[SCALED + NOISE_VOICE]
        for number in range(NOISE_VOICE):
            phase = (state[PHASES + 2 * number] << 8) | state[PHASES + 2 * number + 1]
            increment = (state[INCRS + 2 * number] << 8) | state[INCRS + 2 * number + 1]
            phase = (phase + increment) & 0xFFFF
            state[PHASES + 2 * number] = phase >> 8
            state[PHASES + 2 * number + 1] = phase & 0xFF
            if phase & 0x8000:
                dac += state[SCALED + number]
        output.append(dac >> 2)

        wait -= 1
        if wait == 0:
            state[event.offset] = event.value
            if state[FINISHED]:
                break
            event = next(pending)
            wait = event.wait

    return np.asarray(output, dtype=np.int64)
