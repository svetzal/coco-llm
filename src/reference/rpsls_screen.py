"""The RPSLS board, laid out for a 32 x 16 CoCo text screen.

This is the layout the 6809 will draw, written on the Mac first because 512
cells is small enough that a bad arrangement is unfixable rather than
untidy, and fast enough to iterate here that it is worth getting right before
any of it becomes assembly.

The screen is divided by *whose* it is, which turned out to be a better
organising idea than ranking the parts by importance:

  top     yours. The level name, the keys you press, and how you are doing.
  middle  the play field. Both players' throws, newest on the right, and the
          rule that decided the last one.
  bottom  the machine's. What it expects, and how much it has worked out.

The title is reverse-field, which separates it from the keys below without
spending a blank row on a 16-row screen.

The keys spell the moves out over two rows. A one-row legend of ROC/SPO/PAP
fits and saves a line, but it makes a first-time player decode the thing they
are supposed to be reading fastest. The abbreviations in the history are the
first three letters of these names, so the full spelling above teaches them.

Only the player's share is shown. A YOU/CPU pair adds to 100 and so states one
number twice; and it is given as "5 OF 12 (42%)" rather than a bare percentage
because ties are neither won nor lost, and a lone number invites the reader to
supply a denominator that is not there.

The history's job is letting you catch your own habit before the machine
announces it has. A first version showed both players' throws as the digits
1-5, which is compact and unreadable - "1131 / 5333" is a wall you decode
rather than a pattern you see.

It now shows both players' last seven throws as three-letter names, with the
result letter above them. Three letters distinguish all five moves, which one
cannot - SPOCK and SCISSORS share an initial.

Rows are returned as 32-character strings, uppercased. That is not a style
choice: VDG codes $00-$3F are green on black and cover uppercase only, so
`fit` folds the case rather than letting a lowercase verb reach a screen that
would render it as graphics blocks.
"""

from __future__ import annotations

from rpsls import MOVES, beats, describe

COLUMNS, ROWS = 32, 16
HISTORY = 7
# Derived, not written out, so the legend above the board and the history
# inside it cannot drift apart.
SHORT = tuple(move[:3] for move in MOVES)

TITLE_ROW = 0
KEYS_ROWS = (1, 2)
SCORE_ROW = 3
RESULT_ROW = 5
YOU_ROW = 6
CPU_ROW = 7
REASON_ROW = 9
VERDICT_ROW = 10
EXPECT_ROW = 13
RULES_ROW = 14
MEMORY_ROW = 15

# Drawn black on green ($40-$7F) rather than green on black. The only row
# that is, which is what makes it read as a bar.
INVERSE = frozenset({TITLE_ROW})


def centre(text: str) -> str:
    text = text[:COLUMNS]
    return " " * ((COLUMNS - len(text)) // 2) + text


def fit(text: str) -> str:
    """A row is exactly 32 cells of uppercase. Nothing else can be drawn."""
    return text.upper()[:COLUMNS].ljust(COLUMNS)


def percent(part: int, total: int) -> str:
    return "-" if total == 0 else f"{round(100.0 * part / total)}%"


def render(
    *,
    level: str,
    expects: str | None,
    player_moves: list[int],
    agent_moves: list[int],
    reason: str,
    verdict: str,
    player_wins: int,
    rounds: int,
    rules_known: int,
    memory: int,
) -> list[str]:
    rows = [" " * COLUMNS for _ in range(ROWS)]

    # Yours: what level this is, what to press, how you are doing.
    rows[TITLE_ROW] = fit(centre(level))
    rows[KEYS_ROWS[0]] = fit(" 1 ROCK    2 SPOCK   3 PAPER")
    rows[KEYS_ROWS[1]] = fit(" 4 LIZARD  5 SCISSORS")
    if rounds:
        won = f"YOU HAVE WON {player_wins} OF {rounds} ({percent(player_wins, rounds)})"
    else:
        won = "NO ROUNDS PLAYED YET"
    rows[SCORE_ROW] = fit(f" {won}")

    rows[REASON_ROW] = fit(f" {reason}")
    rows[VERDICT_ROW] = fit(f" {verdict}")

    # The machine's end of the screen.
    plan = "IT HAS NO IDEA YET" if expects is None else f"IT EXPECTS {expects}"
    rows[EXPECT_ROW] = fit(f" {plan}")
    rows[RULES_ROW] = fit(f" RULES  {rules_known:>2}/25")
    rows[MEMORY_ROW] = fit(f" MEMORY {memory:>3}/{rounds}")

    # The play field. Newest on the right, so the current throw is the column
    # the eye finishes on, and the sentence below explains that column.
    # Result sits above the throws rather than below: it is what you look for
    # first, and the two rows under it are the evidence for it.
    recent = player_moves[-HISTORY:]
    against = agent_moves[-HISTORY:]
    marks = " ".join(
        f" {'T' if mine == theirs else 'W' if beats(mine, theirs) else 'L'} "
        for mine, theirs in zip(recent, against, strict=True)
    )
    rows[RESULT_ROW] = fit(f"     {marks}")
    rows[YOU_ROW] = fit(f" YOU {' '.join(SHORT[move] for move in recent)}")
    rows[CPU_ROW] = fit(f" CPU {' '.join(SHORT[move] for move in against)}")
    return rows


def result_lines(player: int, agent: int, result: int) -> tuple[str, str]:
    """The two lines under the keys: why, then who."""
    if player == agent:
        return f"BOTH THREW {MOVES[agent]}", "A TIE"
    if result == 2:
        return describe(player, agent), f"YOU WIN - IT THREW {MOVES[agent]}"
    return describe(agent, player), f"YOU LOSE - IT THREW {MOVES[agent]}"


def frame(rows: list[str]) -> str:
    """A bordered preview, with the reverse-field rows actually reversed."""
    edge = "+" + "-" * COLUMNS + "+"
    drawn = [
        f"|\033[7m{row}\033[0m|" if index in INVERSE else f"|{row}|"
        for index, row in enumerate(rows)
    ]
    return "\n".join([edge, *drawn, edge])
