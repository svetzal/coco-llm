"""The board has to fit a CoCo screen exactly, in characters it can draw."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from rpsls import MOVE_COUNT, MOVES, outcome
from rpsls_screen import (
    BLUE,
    COLUMNS,
    GREEN,
    HISTORY,
    INVERSE,
    MARKS,
    RED,
    RESULT_ROW,
    ROWS,
    SHORT,
    TITLE_ROW,
    cells,
    render,
    result_lines,
    sg4,
)


def board(**overrides) -> list[str]:
    reason, verdict = result_lines(0, 2, outcome(0, 2))
    settings = {
        "level": "THE CATSPAW OF ZETAR",
        "expects": "ROCK",
        "player_moves": [0, 2, 4, 1, 3] * 6,
        "agent_moves": [2, 3, 0, 4, 1] * 6,
        "reason": reason,
        "verdict": verdict,
        "player_wins": 12,
        "rounds": 30,
        "rules_known": 9,
        "memory": 30,
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


def test_the_score_states_its_own_denominator() -> None:
    """A bare percentage invites a denominator that is not there: ties are
    neither won nor lost, so wins over rounds does not sum to 100 with the
    machine's share."""
    for score, rounds in ((0, 10), (10, 10), (5, 10), (12, 30)):
        rows = render(
            level="X",
            expects=None,
            player_moves=[],
            agent_moves=[],
            reason="",
            verdict="",
            player_wins=score,
            rounds=rounds,
            rules_known=0,
            memory=rounds,
        )
        assert f"{score} OF {rounds}" in rows[3]


def test_an_empty_session_says_so_rather_than_showing_zero() -> None:
    rows = board(rounds=0, player_wins=0, player_moves=[], agent_moves=[])
    assert "NO ROUNDS PLAYED" in rows[3]
    assert "%" not in rows[3]


def test_the_title_is_the_only_reverse_field_row() -> None:
    """The bar is what separates it from the keys, instead of a blank row."""
    assert INVERSE == {TITLE_ROW}


def test_the_keys_spell_the_moves_out() -> None:
    legend = board()[1] + board()[2]
    for key, name in enumerate(MOVES, start=1):
        assert f"{key} {name}" in legend


def test_every_abbreviation_is_a_prefix_of_its_name() -> None:
    """The legend spells the moves; the history abbreviates them. If those two
    disagree the player has to learn a mapping nothing on screen states."""
    for short, name in zip(SHORT, MOVES, strict=True):
        assert name.startswith(short)


def test_the_result_row_sits_above_both_throw_rows() -> None:
    rows = board(player_moves=[0, 0, 2], agent_moves=[2, 2, 0])
    assert rows[5].split() == ["L", "L", "W"]
    assert rows[6].split()[1:] == ["ROC", "ROC", "PAP"]
    assert rows[7].split()[1:] == ["PAP", "PAP", "ROC"]


def test_history_is_capped_and_shows_the_most_recent() -> None:
    moves = [index % MOVE_COUNT for index in range(40)]
    rows = board(player_moves=moves, agent_moves=moves[::-1])
    names = rows[6].split()[1:]
    assert len(names) == HISTORY
    assert names[-1] == SHORT[moves[-1]]


def test_every_move_abbreviates_distinctly() -> None:
    """One letter cannot: SPOCK and SCISSORS share an initial."""
    assert len(set(SHORT)) == MOVE_COUNT
    assert {len(short) for short in SHORT} == {3}


def test_memory_is_not_the_round_count() -> None:
    """Reset empties the tables mid-session; the stat must follow the tables.

    Showing rounds here would claim a training set that was just discarded.
    """
    rows = board(rounds=40, memory=3)
    assert "MEMORY   3/40" in rows[15]
    assert "RULES" in rows[14]


def test_no_expectation_is_stated_as_such() -> None:
    assert "NO IDEA" in board(expects=None)[13]


def test_the_screen_is_512_cells() -> None:
    assert len(cells(board())) == COLUMNS * ROWS


def test_result_marks_are_graphics_cells_not_characters() -> None:
    """Bit 7 set is what makes the VDG draw a coloured block rather than a
    letter. Without it the row would read as W, L and T again."""
    rows = board(player_moves=[0, 0, 2], agent_moves=[2, 2, 0])
    row = cells(rows)[RESULT_ROW * COLUMNS : (RESULT_ROW + 1) * COLUMNS]
    marks = [cell for cell in row if cell & 0x80]
    assert len(marks) == 3
    assert all(cell & 0x0F == 0x0F for cell in marks)  # all four quadrants lit


def test_win_loss_and_tie_are_three_different_colours() -> None:
    assert len({MARKS["W"], MARKS["L"], MARKS["T"]}) == 3
    assert MARKS["W"] == sg4(GREEN)
    assert MARKS["L"] == sg4(RED)
    assert MARKS["T"] == sg4(BLUE)


def test_only_the_result_row_holds_graphics() -> None:
    """A stray graphics byte anywhere else would draw as coloured blocks in
    the middle of a sentence."""
    grid = cells(board())
    for index in range(ROWS):
        row = grid[index * COLUMNS : (index + 1) * COLUMNS]
        graphic = [cell for cell in row if cell & 0x80]
        assert bool(graphic) == (index == RESULT_ROW and bool(graphic))
        if index != RESULT_ROW:
            assert not graphic


def test_the_title_row_is_the_inverse_set() -> None:
    grid = cells(board())
    title = grid[TITLE_ROW * COLUMNS : (TITLE_ROW + 1) * COLUMNS]
    assert all(0x40 <= cell <= 0x7F for cell in title)
