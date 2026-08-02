import json
from pathlib import Path

import pytest
from melody_tokens import (
    HIGHEST_RELATIVE,
    HOLD,
    LOWEST_RELATIVE,
    MELODY_TOKENS,
    METRES,
    MODES,
    REST,
    Tune,
    chord_token,
    describe,
    metre_token,
    mode_token,
    pitch_token,
    rows_per_bar,
    token_name,
)

CORPUS = Path(__file__).parents[1] / "experiments" / "data" / "EXP-010-chorales.jsonl"


def sample_tune(**overrides) -> Tune:
    fields = {
        "source": "test",
        "title": "Test",
        "mode": "minor",
        "metre": "4/4",
        "tonic": "G",
        "melody": (0, HOLD, 7, REST),
        "chords": (0, 0, 4, 4),
        "beats": (0, 1, 2, 3),
    }
    fields.update(overrides)
    return Tune(**fields)


def test_pitch_tokens_cover_the_measured_range() -> None:
    assert pitch_token(LOWEST_RELATIVE) == 0
    assert pitch_token(HIGHEST_RELATIVE) == HIGHEST_RELATIVE - LOWEST_RELATIVE
    assert pitch_token(HIGHEST_RELATIVE + 1) is None
    assert pitch_token(LOWEST_RELATIVE - 1) is None


def test_every_pitch_token_is_below_the_control_tokens() -> None:
    for relative in range(LOWEST_RELATIVE, HIGHEST_RELATIVE + 1):
        assert pitch_token(relative) < HOLD

    assert HOLD < REST < MELODY_TOKENS


def test_token_names_are_degrees_with_an_octave_marker() -> None:
    assert token_name(pitch_token(0)) == "1"
    assert token_name(pitch_token(7)) == "5"
    assert token_name(pitch_token(11)) == "7"
    assert token_name(pitch_token(12)) == "1+1"
    assert token_name(HOLD) == "HOLD"
    assert token_name(REST) == "REST"


def test_the_raised_seventh_is_representable() -> None:
    # In minor this is the leading tone. Losing it would remove the cadence,
    # which is the structure the experiment is trying to learn.
    assert pitch_token(11) is not None
    assert token_name(pitch_token(11)) == "7"


def test_mode_and_metre_tokens_match_the_surveyed_corpus() -> None:
    assert MODES == ("major", "minor")
    assert mode_token("major") == 0
    assert mode_token("minor") == 1
    assert metre_token("4/4") in range(len(METRES))
    assert metre_token("7/8") is None


def test_dance_metres_were_appended_not_inserted() -> None:
    # Appending keeps the chorale corpus's metre tokens valid without
    # re-extracting it.
    assert METRES[:3] == ("4/4", "3/4", "3/2")
    assert metre_token("6/8") is not None


def test_row_resolution_changes_bar_length() -> None:
    assert rows_per_bar("2/4", 0.25) == 8  # a reel in running sixteenths
    assert rows_per_bar("6/8", 0.25) == 12  # a jig
    assert rows_per_bar("4/4", 0.5) == 8  # a chorale in eighths


def test_chord_tokens_are_zero_based_scale_degrees() -> None:
    assert chord_token(1) == 0
    assert chord_token(7) == 6

    for bad in (0, 8, -1):
        with pytest.raises(ValueError, match="outside 1..7"):
            chord_token(bad)


def test_rows_per_bar_follows_the_metre() -> None:
    assert rows_per_bar("4/4") == 8
    assert rows_per_bar("3/4") == 6
    assert rows_per_bar("3/2") == 12


def test_a_tune_rejects_streams_of_different_lengths() -> None:
    with pytest.raises(ValueError, match="different lengths"):
        sample_tune(beats=(0, 1))


def test_a_tune_round_trips_through_json() -> None:
    tune = sample_tune()

    assert Tune.from_json(json.loads(json.dumps(tune.to_json()))) == tune


def test_describe_renders_leading_tokens() -> None:
    assert describe(sample_tune(), limit=4) == "1 HOLD 5 REST"


@pytest.mark.skipif(not CORPUS.exists(), reason="corpus not extracted")
def test_the_extracted_corpus_is_well_formed() -> None:
    lines = CORPUS.read_text(encoding="utf-8").splitlines()
    tunes = [Tune.from_json(json.loads(line)) for line in lines if line.strip()]

    assert len(tunes) > 200

    for tune in tunes:
        assert tune.mode in MODES
        assert tune.metre in METRES
        assert tune.rows > 0
        assert all(0 <= token < MELODY_TOKENS for token in tune.melody)
        assert all(0 <= token < 7 for token in tune.chords)
        assert all(0 <= beat < rows_per_bar(tune.metre) for beat in tune.beats)


@pytest.mark.skipif(not CORPUS.exists(), reason="corpus not extracted")
def test_the_holdout_is_whole_tunes_and_disjoint() -> None:
    payloads = [
        json.loads(line)
        for line in CORPUS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    train = {p["source"] for p in payloads if p["split"] == "train"}
    holdout = {p["source"] for p in payloads if p["split"] == "holdout"}

    assert holdout
    assert not train & holdout
