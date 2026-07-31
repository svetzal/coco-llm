import json
from pathlib import Path

import pytest
from duel_arena import (
    CAPTURE_SCHEMA,
    MOVE_COUNT,
    PLAYER_BY_NAME,
    Arena,
    Capture,
    append_capture,
    generate_stream,
    load_captures,
    stream_from_runs,
)
from mimic_lm import build_candidate_predictors, evaluate_stream


def make_capture(runs: tuple[tuple[int, ...], ...]) -> Capture:
    return Capture(
        label="test-01",
        recorded_utc="2026-07-31T00:00:00+00:00",
        tick_hz=10,
        runs=runs,
        outcomes=tuple("caught" for _ in runs),
    )


def test_capture_round_trips_through_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "captures.jsonl"
    original = make_capture(((1, 2, 3), (4, 5, 6, 7)))
    append_capture(path, original)

    loaded = load_captures(path)

    assert len(loaded) == 1
    assert loaded[0] == original


def test_appending_preserves_earlier_sessions(tmp_path: Path) -> None:
    path = tmp_path / "captures.jsonl"
    append_capture(path, make_capture(((1, 1, 1),)))
    append_capture(path, make_capture(((2, 2),)))

    loaded = load_captures(path)

    assert [capture.ticks for capture in loaded] == [3, 2]


def test_capture_ticks_count_every_run() -> None:
    assert make_capture(((1, 2, 3), (4, 5))).ticks == 5


def test_loading_rejects_an_unknown_schema(tmp_path: Path) -> None:
    path = tmp_path / "captures.jsonl"
    path.write_text(json.dumps({"schema": "something-else", "runs": []}) + "\n")

    with pytest.raises(ValueError, match="unsupported capture schema"):
        load_captures(path)


def test_loading_rejects_a_move_outside_the_vocabulary(tmp_path: Path) -> None:
    path = tmp_path / "captures.jsonl"
    payload = make_capture(((1, 2),)).to_json()
    payload["runs"][0]["moves"] = [1, MOVE_COUNT]
    path.write_text(json.dumps(payload) + "\n")

    with pytest.raises(ValueError, match="move out of range"):
        load_captures(path)


def test_written_payload_declares_the_current_schema() -> None:
    assert make_capture(((0,),)).to_json()["schema"] == CAPTURE_SCHEMA


def test_replay_reproduces_the_arena_a_live_session_saw() -> None:
    moves = (3, 3, 2, 1, 8, 7, 7, 6, 5, 5, 4, 3)
    live = Arena()
    expected = []
    for move in moves:
        expected.append(live.record())
        live.apply(move)

    replayed = stream_from_runs([moves])

    assert [record for record, _ in replayed] == expected


def test_replay_resets_the_arena_between_runs() -> None:
    single = stream_from_runs([(3, 3, 3)])
    paired = stream_from_runs([(3, 3, 3), (3, 3, 3)])

    assert paired[:3] == single
    assert paired[3:] == single


def test_replay_length_is_the_total_tick_count() -> None:
    capture = make_capture(((1, 2, 3), (4, 5)))

    assert len(capture.stream()) == capture.ticks


def test_captured_streams_score_through_the_same_harness() -> None:
    synthetic = generate_stream(PLAYER_BY_NAME["HABIT"], ticks=300, seed=5)
    capture = make_capture((tuple(move for _, move in synthetic),))
    predictors = build_candidate_predictors(embeddings=[4], shifts=[4], seed=5)

    results = evaluate_stream(capture.stream(), predictors, window=100)

    assert len(results) == len(predictors)
    assert all(0.0 <= result.window_accuracy <= 1.0 for result in results)


def test_the_candidate_set_is_identical_for_sweeps_and_replays() -> None:
    first = build_candidate_predictors(embeddings=[4, 6], shifts=[4, 3], seed=11)
    second = build_candidate_predictors(embeddings=[4, 6], shifts=[4, 3], seed=11)

    assert [item.name for item in first] == [item.name for item in second]
    assert len(first) == 4 + 2 * 2 * 2


def test_the_arena_reports_a_catch_only_when_adjacent() -> None:
    assert Arena(player=(10, 10), opponent=(11, 11)).is_caught()
    assert Arena(player=(10, 10), opponent=(10, 10)).is_caught()
    assert not Arena(player=(10, 10), opponent=(12, 10)).is_caught()


def test_a_pinned_chaser_never_occupies_the_player_cell() -> None:
    # Phase A relies on this: bearing must stay defined for a whole stream even
    # when a motionless player lets the chaser close all the way in.
    arena = Arena()
    for _ in range(600):
        arena.apply(0)

        assert arena.delta != (0, 0)
