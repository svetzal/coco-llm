"""The steady sample clock: the reference for EXP-018.

EXP-009's player does its row and tick work between samples, and each
piece of that work stretches the sample it borrows by most of a period.
At a row change that is five stretched samples in a row, 8.33 times a
second in the demo tune, and a sustained note's phase slips by about four
periods every time. That is the warble heard on the CoCo 3.

This player has no row or tick work at all. The tune is compiled ahead of
time into a stream of events, each one byte written to one address after
a wait of so many samples, and the sample loop applies at most one event
per sample through a path padded to cost exactly what the idle path
costs. Every sample then costs the same number of cycles, whatever the
tune is doing, and the sample clock never moves.

The compiler here, `compile_rows`, is mirrored line for line by
`src/6809/steady_compile.asm`, which the melody demo runs on the CoCo
after it has composed. Both take the same row bytes and must emit the
same stream; a parity test checks that they do. An address outside the
player's page, the playback cursor on the screen for instance, is an
event like any other: the reference ignores it, the CoCo draws it.

The state the events write is EXP-009's: phase accumulators, increments
and pre-shifted volumes. Decay is computed by the compiler, so the stream
carries the resulting volumes. The sample arithmetic is EXP-009's, byte
for byte, which is what makes the two players comparable.
"""

from __future__ import annotations

from collections.abc import Sequence
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

# The direct page of steady_player.asm. The parity test checks the
# assembled symbols against these offsets.
PAGE = 0x2000
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
EVENT_BYTES = 4

# Row cells as the player's tune data encodes them: note code, volume, decay.
NOTE_HOLD_CODE = 0
NOTE_OFF_CODE = 1
LOW_NOTE = 12

Row = Sequence[tuple[int, int, int]]


@dataclass(frozen=True)
class Event:
    """One byte written to one address after `wait` more samples."""

    wait: int
    address: int
    value: int


@dataclass(frozen=True)
class Cursor:
    """A playback cursor the stream draws: one cell per `rows_per_cell`
    rows along `track`, blanked behind it."""

    track: int
    blank: int
    mark: int
    rows_per_cell: int = 4


def encode_rows(tune: Tune) -> list[list[tuple[int, int, int]]]:
    """A tune's cells as the byte triples the player's row data holds."""
    rows = []
    for row in tune.rows:
        encoded = []
        for cell in row:
            if cell.note == NOTE_HOLD:
                encoded.append((NOTE_HOLD_CODE, 0, 0))
            elif cell.note == NOTE_OFF:
                encoded.append((NOTE_OFF_CODE, 0, 0))
            else:
                encoded.append(
                    (cell.note, min(MAX_VOLUME, cell.volume), min(255, cell.decay))
                )
        rows.append(encoded)
    return rows


def compile_rows(
    rows: Sequence[Row],
    *,
    ticks_per_row: int,
    samples_per_tick: int,
    sample_rate: int,
    cursor: Cursor | None = None,
) -> list[Event]:
    """Turn row bytes into the event stream the player replays.

    Mirrors steady_compile.asm exactly, including the order of writes and
    where a long wait is split. A tick is `samples_per_tick` samples. Its
    writes land one per sample after the tick's first sample, so the first
    sample of every tick is on the previous state, as in the other
    players. `elapsed` is the samples since the last event was due; it is
    kept at 255 or below by emitting a filler event whenever it grows past
    that, so the 6809 can hold it in a byte's worth of arithmetic.
    """
    if samples_per_tick < 1 + WRITES_PER_CELL * VOICE_COUNT + 2:
        raise ValueError(f"{samples_per_tick} samples per tick cannot hold a row")
    if samples_per_tick > MAX_WAIT:
        raise ValueError(f"{samples_per_tick} samples per tick does not fit a byte")

    events: list[Event] = []
    volumes = [0] * VOICE_COUNT
    decays = [0] * VOICE_COUNT
    elapsed = 0
    previous_cell = 0

    def emit(address: int, value: int) -> None:
        nonlocal elapsed
        wait = elapsed + 1
        if wait > MAX_WAIT:
            events.append(Event(MAX_WAIT, PAGE + SCRATCH, 0))
            wait -= MAX_WAIT
        events.append(Event(wait, address, value))
        elapsed = 0

    for row_number, row in enumerate(rows):
        if len(row) != VOICE_COUNT:
            raise ValueError(f"row {row_number} has {len(row)} cells")
        for tick in range(ticks_per_row):
            written = len(events)
            if tick == 0:
                if cursor and row_number % cursor.rows_per_cell == 0:
                    cell = row_number // cursor.rows_per_cell
                    emit(cursor.track + previous_cell, cursor.blank)
                    emit(cursor.track + cell, cursor.mark)
                    previous_cell = cell
                for number in range(VOICE_COUNT):
                    note, volume, decay = row[number]
                    if note == NOTE_HOLD_CODE:
                        continue
                    if note == NOTE_OFF_CODE:
                        volumes[number] = 0
                        emit(PAGE + SCALED + number, 0)
                        continue
                    if number != NOISE_VOICE:
                        increment = note_increment(note, sample_rate)
                        emit(PAGE + INCRS + 2 * number, increment >> 8)
                        emit(PAGE + INCRS + 2 * number + 1, increment & 0xFF)
                        emit(PAGE + PHASES + 2 * number, 0)
                        emit(PAGE + PHASES + 2 * number + 1, 0)
                    volumes[number] = volume
                    decays[number] = decay
                    emit(PAGE + SCALED + number, volume << 2)
            else:
                for number in range(VOICE_COUNT):
                    if decays[number] and volumes[number]:
                        volumes[number] = max(0, volumes[number] - decays[number])
                        emit(PAGE + SCALED + number, volumes[number] << 2)
            # Fillers count as events but not as this tick's writes.
            writes = sum(
                1 for event in events[written:] if event.address != PAGE + SCRATCH
            )
            elapsed += samples_per_tick - writes
            if elapsed > MAX_WAIT:
                events.append(Event(MAX_WAIT, PAGE + SCRATCH, 0))
                elapsed -= MAX_WAIT

    events.append(Event(elapsed, PAGE + FINISHED, 1))
    return events


def compile_events(tune: Tune, sample_rate: int) -> list[Event]:
    """A whole tune, as the standalone builds carry it."""
    samples_per_tick = round(sample_rate / tune.tick_hz)
    return compile_rows(
        encode_rows(tune),
        ticks_per_row=tune.ticks_per_row,
        samples_per_tick=samples_per_tick,
        sample_rate=sample_rate,
    )


def stream_bytes(events: Sequence[Event]) -> bytes:
    """The stream as the player reads it: wait, address high, address low,
    value, ... and a spare byte after the last event, which the player
    reads as a wait it never uses."""
    out = bytearray()
    for event in events:
        out += bytes(
            (event.wait, event.address >> 8, event.address & 0xFF, event.value)
        )
    out.append(0)
    return bytes(out)


def render(tune: Tune, *, sample_rate: int) -> NDArray[np.int64]:
    """One pass of the tune, exactly as the player produces it."""
    return replay(compile_events(tune, sample_rate))


def replay(events: Sequence[Event]) -> NDArray[np.int64]:
    """The DAC stream a compiled event list produces."""
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
            if PAGE <= event.address < PAGE + PAGE_BYTES:
                state[event.address - PAGE] = event.value
            if state[FINISHED]:
                break
            event = next(pending)
            wait = event.wait

    return np.asarray(output, dtype=np.int64)
