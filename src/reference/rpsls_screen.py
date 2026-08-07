"""The RPSLS board, laid out for a 32 x 16 CoCo text screen.

This is the layout the 6809 will draw, written on the Mac first because 512
cells is small enough that a bad arrangement is unfixable rather than
untidy, and fast enough to iterate here that it is worth getting right before
any of it becomes assembly.

Five things have to share the screen, and they were ranked by how often a
player's eye goes to them:

  the level name   once, at the top, the EXP-012 generator's line.
  its expectation  every round, before you throw. This is the honest bit and
                   it earns the highest position in the body.
  your keys        every round, but read once and then remembered. Compact.
  what happened    every round, and it carries the rule being taught, so it
                   gets its own two lines rather than being crowded.
  the tallies      glanced at. Bottom, and the win split is the only thing
                   given its own centred block.

The history is digits rather than letters because 1-5 are the keys you press,
so it needs no legend, and because SPOCK and SCISSORS both start with S. It
also does the demo's real work: a column of your own throws is where you see
your habit before the machine tells you it has found one.

Rows are returned as 32-character strings, uppercased. That is not a style
choice: VDG codes $00-$3F are green on black and cover uppercase only, so
`fit` folds the case rather than letting a lowercase verb reach a screen that
would render it as graphics blocks.
"""

from __future__ import annotations

from rpsls import MOVES, describe

COLUMNS, ROWS = 32, 16
HISTORY = 16

TITLE_ROW = 0
EXPECT_ROW = 2
KEYS_ROWS = (4, 5)
REASON_ROW = 7
VERDICT_ROW = 8
HISTORY_ROWS = (10, 11)
SPLIT_ROWS = (13, 14)
STATS_ROW = 15


def centre(text: str) -> str:
    text = text[:COLUMNS]
    return " " * ((COLUMNS - len(text)) // 2) + text


def fit(text: str) -> str:
    """A row is exactly 32 cells of uppercase. Nothing else can be drawn."""
    return text.upper()[:COLUMNS].ljust(COLUMNS)


def percent(part: float, total: int) -> str:
    return "  - " if total == 0 else f"{round(100.0 * part / total):>3}%"


def render(
    *,
    level: str,
    expects: str | None,
    player_moves: list[int],
    agent_moves: list[int],
    reason: str,
    verdict: str,
    player_score: float,
    rounds: int,
    rules_known: int,
) -> list[str]:
    rows = [" " * COLUMNS for _ in range(ROWS)]

    rows[TITLE_ROW] = fit(centre(level))

    plan = "IT HAS NO IDEA YET" if expects is None else f"IT EXPECTS {expects}"
    rows[EXPECT_ROW] = fit(f" {plan}")

    rows[KEYS_ROWS[0]] = fit(" 1 ROCK    2 SPOCK   3 PAPER")
    rows[KEYS_ROWS[1]] = fit(" 4 LIZARD  5 SCISSORS")

    rows[REASON_ROW] = fit(f" {reason}")
    rows[VERDICT_ROW] = fit(f" {verdict}")

    # Most recent on the right, so the newest throw lands where the eye
    # already is after reading the line.
    def trail(moves: list[int]) -> str:
        return "".join(str(move + 1) for move in moves[-HISTORY:]).rjust(HISTORY)

    rows[HISTORY_ROWS[0]] = fit(f" YOU {trail(player_moves)}")
    rows[HISTORY_ROWS[1]] = fit(f" CPU {trail(agent_moves)}")

    # The one block that is centred, because it is the score and the score is
    # the argument. A tie counts a half to each, so the two always sum to 100.
    rows[SPLIT_ROWS[0]] = fit(centre(f"YOU {percent(player_score, rounds)}"))
    rows[SPLIT_ROWS[1]] = fit(centre(f"CPU {percent(rounds - player_score, rounds)}"))

    rows[STATS_ROW] = fit(f" RULES {rules_known:>2}/25     SEEN {rounds:>3}")
    return rows


def result_lines(player: int, agent: int, result: int) -> tuple[str, str]:
    """The two lines under the keys: why, then who."""
    if player == agent:
        return f"BOTH THREW {MOVES[agent]}", "A TIE"
    if result == 2:
        return describe(player, agent), f"YOU WIN - IT THREW {MOVES[agent]}"
    return describe(agent, player), f"YOU LOSE - IT THREW {MOVES[agent]}"


def frame(rows: list[str]) -> str:
    """A bordered preview, so 32 columns are visible as 32 columns."""
    edge = "+" + "-" * COLUMNS + "+"
    return "\n".join([edge, *(f"|{row}|" for row in rows), edge])
