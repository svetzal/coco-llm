"""The board has to fit a CoCo screen exactly, in characters it can draw."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from rpsls import MOVE_COUNT, MOVES, outcome
from rpsls_screen import COLUMNS, HISTORY, ROWS, render, result_lines


def board(**overrides) -> list[str]:
    reason, verdict = result_lines(0, 2, outcome(0, 2))
    settings = {
        "level": "THE CATSPAW OF ZETAR",
        "expects": "ROCK",
        "player_moves": [0, 2, 4, 1, 3] * 6,
        "agent_moves": [2, 3, 0, 4, 1] * 6,
        "reason": reason,
        "verdict": verdict,
        "player_score": 12.5,
        "rounds": 30,
        "rules_known": 9,
    }
    settings.update(overrides)
    return render(**settings)


def test_the_board_is_exactly_a_coco_screen() -> None:
    rows = board()
    assert len(rows) == ROWS
    assert {len(row) for row in rows} == {COLUMNS}


def test_nothing_lowercase_reaches_the_screen() -> None:
    """VDG codes $00-$3F are uppercase only; a lowercase verb draws garbage."""
    for row in board():
        assert row == row.upper(), row


def test_the_longest_move_name_still_fits() -> None:
    longest = max(MOVES, key=len)
    for row in board(expects=longest):
        assert len(row) == COLUMNS


def test_a_long_level_name_cannot_overflow_its_row() -> None:
    rows = board(level="THE ENTERPRISE INCIDENT OF PLATO'S STEPCHILDREN")
    assert len(rows[0]) == COLUMNS


def test_the_split_always_sums_to_a_hundred() -> None:
    """A tie counts a half to each, so the two shares are complements."""
    for score, rounds in ((0.0, 10), (10.0, 10), (5.0, 10), (12.5, 30)):
        rows = render(
            level="X",
            expects=None,
            player_moves=[],
            agent_moves=[],
            reason="",
            verdict="",
            player_score=score,
            rounds=rounds,
            rules_known=0,
        )
        you = int(rows[13].strip().split()[1].rstrip("%"))
        cpu = int(rows[14].strip().split()[1].rstrip("%"))
        assert you + cpu == 100


def test_an_empty_session_shows_no_percentage() -> None:
    rows = board(rounds=0, player_score=0.0, player_moves=[], agent_moves=[])
    assert "-" in rows[13]
    assert "%" not in rows[13]


def test_history_is_capped_and_shows_the_most_recent() -> None:
    moves = [index % MOVE_COUNT for index in range(40)]
    rows = board(player_moves=moves)
    trail = rows[10].split()[1]
    assert len(trail) == HISTORY
    assert trail.endswith(str(moves[-1] + 1))


def test_no_expectation_is_stated_as_such() -> None:
    assert "NO IDEA" in board(expects=None)[2]
