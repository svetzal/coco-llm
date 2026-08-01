from itertools import pairwise

import numpy as np
from coco_synth import (
    DAC_MAX,
    LFSR_SEED,
    MAX_VOLUME,
    NOTE_HOLD,
    NOTE_OFF,
    PHASE_MASK,
    VOICE_COUNT,
    Cell,
    Synth,
    Tune,
    Voice,
    build_increment_table,
    build_mix_table,
    demo_tune,
    note_frequency,
    note_increment,
    render,
    to_waveform,
)

RATE = 7300


def test_concert_a_is_440_hz() -> None:
    assert note_frequency(69) == 440.0


def test_an_octave_doubles_the_increment() -> None:
    low = note_increment(57, RATE)
    high = note_increment(69, RATE)

    assert abs(high - 2 * low) <= 1


def test_increments_stay_inside_sixteen_bits() -> None:
    table = build_increment_table(12, 108, RATE)

    assert all(1 <= value <= PHASE_MASK for value in table.values())


def test_mix_table_sums_the_voices_that_are_high() -> None:
    table = build_mix_table([1, 2, 4, 8])

    assert table[0b0000] == 0
    assert table[0b0001] == 1
    assert table[0b1010] == 10
    assert table[0b1111] == 15


def test_four_voices_at_full_volume_stay_inside_the_dac() -> None:
    table = build_mix_table([MAX_VOLUME] * VOICE_COUNT)

    assert int(table.max()) == MAX_VOLUME * VOICE_COUNT
    assert int(table.max()) <= DAC_MAX


def test_a_square_voice_alternates_high_and_low() -> None:
    voice = Voice(increment=PHASE_MASK // 8)
    bits = [voice.step() for _ in range(64)]

    assert set(bits) == {0, 1}


def test_a_square_voice_has_the_period_its_increment_implies() -> None:
    voice = Voice(increment=1 << 12)
    bits = [voice.step() for _ in range(64)]
    transitions = sum(1 for a, b in pairwise(bits) if a != b)

    # 1<<12 wraps 16 bits every 16 samples, so 64 samples hold four full
    # cycles, and each cycle has two edges.
    assert transitions == 8


def test_a_noise_voice_only_clocks_when_its_phase_wraps() -> None:
    voice = Voice(increment=1, noise=True)
    voice.step()

    assert voice.lfsr == LFSR_SEED


def test_a_noise_voice_does_not_repeat_quickly() -> None:
    voice = Voice(increment=PHASE_MASK, noise=True)
    bits = [voice.step() for _ in range(512)]

    assert 0 in bits and 1 in bits
    assert bits[:64] != bits[64:128]


def test_a_held_note_leaves_the_voice_alone() -> None:
    synth = Synth(sample_rate=RATE)
    synth.apply_row([Cell(note=69, volume=9)] + [Cell()] * 3)
    increment = synth.voices[0].increment
    synth.apply_row([Cell(note=NOTE_HOLD)] * VOICE_COUNT)

    assert synth.voices[0].increment == increment
    assert synth.voices[0].volume == 9


def test_note_off_silences_only_that_voice() -> None:
    synth = Synth(sample_rate=RATE)
    synth.apply_row([Cell(note=69, volume=9), Cell(note=60, volume=7), Cell(), Cell()])
    synth.apply_row([Cell(note=NOTE_OFF), Cell(note=NOTE_HOLD), Cell(), Cell()])

    assert synth.voices[0].volume == 0
    assert synth.voices[1].volume == 7


def test_decay_reduces_volume_once_per_tick_and_stops_at_zero() -> None:
    synth = Synth(sample_rate=RATE)
    synth.apply_row([Cell(note=60, volume=6, decay=2)] + [Cell()] * 3)

    for _ in range(10):
        synth.apply_tick()

    assert synth.voices[0].volume == 0


def test_the_mix_table_follows_a_decaying_voice() -> None:
    synth = Synth(sample_rate=RATE)
    synth.apply_row([Cell(note=60, volume=8, decay=4)] + [Cell()] * 3)
    before = int(synth.mix_table[0b0001])
    synth.apply_tick()

    assert int(synth.mix_table[0b0001]) < before


def test_every_sample_is_a_legal_dac_value() -> None:
    dac = render(demo_tune(), sample_rate=RATE)

    assert int(dac.min()) >= 0
    assert int(dac.max()) <= DAC_MAX


def test_rendering_is_deterministic() -> None:
    tune = demo_tune()

    assert np.array_equal(
        render(tune, sample_rate=RATE), render(tune, sample_rate=RATE)
    )


def test_render_length_matches_the_declared_tempo() -> None:
    tune = demo_tune()
    dac = render(tune, sample_rate=RATE)
    expected = len(tune.rows) * tune.ticks_per_row * round(RATE / tune.tick_hz)

    assert len(dac) == expected
    assert abs(len(dac) / RATE - tune.seconds) < 0.05


def test_silence_renders_as_a_constant() -> None:
    quiet = Tune(name="quiet", rows=((Cell(note=NOTE_OFF),) * VOICE_COUNT,))
    dac = render(quiet, sample_rate=RATE)

    assert len(set(dac.tolist())) == 1


def test_waveform_is_centred_and_within_range() -> None:
    waveform = to_waveform(render(demo_tune(), sample_rate=RATE))

    assert waveform.dtype == np.int16
    assert abs(int(waveform.mean())) < 3000
    assert int(np.abs(waveform).max()) <= 32767


def test_the_demo_tune_produces_its_intended_pitches() -> None:
    tune = demo_tune()
    dac = render(tune, sample_rate=RATE)
    row = int(RATE / tune.tick_hz) * tune.ticks_per_row
    segment = dac[:row].astype(float)
    segment -= segment.mean()
    spectrum = np.abs(np.fft.rfft(segment * np.hanning(len(segment))))
    frequencies = np.fft.rfftfreq(len(segment), 1 / RATE)
    floor = float(np.median(spectrum))

    # Row 0 sounds A2 bass, A3 arpeggio, and A4 melody together.
    for note in (45, 57, 69):
        target = note_frequency(note)
        window = (frequencies > target - 12) & (frequencies < target + 12)

        assert float(spectrum[window].max()) > floor * 8
