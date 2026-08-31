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
spending a blank row on a 16-row screen. It spans the full width, so the body
does too: an indented body under a full-width bar reads as a misalignment
rather than as a margin, which is what a one-column indent looked like. The body is black on green, the
CoCo's own look; the bar is green on black. src/6809/text_screen.asm holds
that convention for both experiments, after this one was built with the two
sets the wrong way round and came out inverted.

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
result above them as a block of colour rather than a letter: green won, red
lost, blue tied. A row of letters has to be read left to right; a row of
colour is one glance, and a losing streak is a red bar you cannot miss.

Three letters distinguish all five moves, which one cannot - SPOCK and
SCISSORS share an initial.

Rows are returned as 32-character strings, uppercased. That is not a style
choice: both VDG character sets cover uppercase only, so `fit` folds the case
rather than letting a lowercase verb reach a screen that would draw it as
graphics blocks.
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
# Only used by the three verb sentences too long for one row.
CONTINUE_ROW = 11
# The only row whose contents are graphics cells rather than characters.
GRAPHIC_ROWS = frozenset({RESULT_ROW})
EXPECT_ROW = 13
RULES_ROW = 14
MEMORY_ROW = 15

# The rows drawn from the reversed set, green on black. The body is black on
# green - the CoCo's own look and the convention across this series. The
# title bar reverses to read as a bar, and the play field reverses so the
# score marks' red, green and blue sit on black instead of the body green,
# with the YOU and CPU trails on the same ground.
REVERSED = frozenset({TITLE_ROW, RESULT_ROW, YOU_ROW, CPU_ROW})

# Semigraphics-4: a cell byte is 1 C C C L L L L. Bit 7 marks the cell as
# graphic rather than a character, bits 6-4 choose one of eight colours, and
# bits 3-0 light the four quadrants - so $0F is a solid block.
#
# The VDG's colour order is green, yellow, blue, red, buff, cyan, magenta,
# orange. Confirmed on the emulator: the marks come out green for a win, red
# for a loss and blue for a tie, as intended.
SG4_SOLID = 0x0F
GREEN, YELLOW, BLUE, RED = 0, 1, 2, 3
# Each set carries its own blank and it falls out of the same arithmetic as
# the letters: a space is $60 black-on-green and $20 green-on-black. Nothing
# needs to special-case it, which is why `cells` below does not.


def sg4(colour: int) -> int:
    return 0x80 | (colour << 4) | SG4_SOLID


# Green won, red lost, blue tied. Kept as letters inside the rendered rows so
# the layout stays readable in tests and previews; `cells` turns them into the
# bytes the screen actually holds.
MARKS = {"W": sg4(GREEN), "L": sg4(RED), "T": sg4(BLUE)}


def centre(text: str) -> str:
    text = text[:COLUMNS]
    return " " * ((COLUMNS - len(text)) // 2) + text


def fit(text: str) -> str:
    """A row is exactly 32 cells of uppercase. Nothing else can be drawn."""
    return text.upper()[:COLUMNS].ljust(COLUMNS)


def percent(part: int, total: int) -> str:
    """Round half up, in integers.

    round() rounds half to even, which the 6809 cannot do without code that
    exists for no other reason, and which nobody expects of a score. Adding
    half the divisor before dividing is one instruction there and the same
    answer here.
    """
    if total == 0:
        return "-"
    return f"{(100 * part + total // 2) // total}%"


def render(
    *,
    level: str,
    expects: str | None,
    player_moves: list[int],
    agent_moves: list[int],
    reason: str,
    verdict: str,
    continuation: str = "",
    player_wins: int,
    rounds: int,
    rules_known: int,
    memory: int,
) -> list[str]:
    rows = [" " * COLUMNS for _ in range(ROWS)]

    # Yours: what level this is, what to press, how you are doing.
    rows[TITLE_ROW] = fit(centre(level))
    rows[KEYS_ROWS[0]] = fit("1 ROCK    2 SPOCK   3 PAPER")
    rows[KEYS_ROWS[1]] = fit("4 LIZARD  5 SCISSORS")
    if rounds:
        won = f"YOU HAVE WON {player_wins} OF {rounds} ({percent(player_wins, rounds)})"
    else:
        won = "NO ROUNDS PLAYED YET"
    rows[SCORE_ROW] = fit(won)

    rows[REASON_ROW] = fit(reason)
    rows[VERDICT_ROW] = fit(verdict)
    rows[CONTINUE_ROW] = fit(continuation)

    # The machine's end of the screen.
    plan = "IT HAS NO IDEA YET" if expects is None else f"IT EXPECTS {expects}"
    rows[EXPECT_ROW] = fit(plan)
    rows[RULES_ROW] = fit(f"RULES  {rules_known:>2}/25")
    rows[MEMORY_ROW] = fit(f"MEMORY {memory:>3}/{rounds}")

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
    rows[RESULT_ROW] = fit(f"    {marks}")
    rows[YOU_ROW] = fit(f"YOU {' '.join(SHORT[move] for move in recent)}")
    rows[CPU_ROW] = fit(f"CPU {' '.join(SHORT[move] for move in against)}")
    return rows


def result_lines(player: int, agent: int, result: int) -> tuple[str, str]:
    """The two result rows: who threw what, then who won and why.

    The throws go on one line with the machine's right-aligned, so the two
    players face each other across the row. The verdict comes before the rule
    on the line below, because the outcome is what you look for and the rule
    is the explanation you read second.
    """
    throws = f"YOU: {MOVES[player]}"
    against = f"CPU: {MOVES[agent]}"
    facing = throws + " " * (COLUMNS - len(throws) - len(against)) + against

    if player == agent:
        return (facing, *wrapped("A TIE", f"BOTH THREW {MOVES[agent]}"))
    verdict = "YOU WIN" if result == 2 else "YOU LOSE"
    winner, loser = (player, agent) if result == 2 else (agent, player)
    return (facing, *wrapped(verdict, describe(winner, loser)))


def wrapped(verdict: str, rule: str) -> tuple[str, str]:
    """The verdict and rule over one row, or two when they will not fit.

    "YOU LOSE, SCISSORS DECAPITATES LIZARD" is 38 columns against 32, and two
    other pairs also overflow. No verdict word is short enough to rescue it -
    even "LOST," leaves the longest one column over - so the sentence wraps.

    The continuation hangs under the rule rather than under the verdict, so
    the wrapped word reads as part of the sentence it belongs to instead of
    starting a new statement.
    """
    lead = f"{verdict}, "
    words = rule.upper().split()
    if len(lead) + len(" ".join(words)) <= COLUMNS:
        return lead + " ".join(words), ""
    kept = len(words)
    while kept > 1 and len(lead) + len(" ".join(words[:kept])) > COLUMNS:
        kept -= 1
    return lead + " ".join(words[:kept]), " " * len(lead) + " ".join(words[kept:])


def cells(rows: list[str]) -> list[int]:
    """The 512 bytes the CoCo screen actually holds.

    Text is the low six bits of uppercase ASCII; the result row's letters
    become solid colour blocks. This is the form the 6809 writes and the form
    a parity test compares, so it is derived here rather than in the port.
    """
    out: list[int] = []
    for index, row in enumerate(rows):
        graphic = index in GRAPHIC_ROWS
        for character in row:
            if graphic and character in MARKS:
                out.append(MARKS[character])
            elif index in REVERSED:
                out.append(ord(character) & 0x3F)
            else:
                out.append(ord(character) | 0x40)
    return out


PREVIEW = {"W": "\033[42m \033[0m", "L": "\033[41m \033[0m", "T": "\033[44m \033[0m"}


def frame(rows: list[str]) -> str:
    """A bordered preview, with the reverse-field rows actually reversed."""
    edge = "+" + "-" * COLUMNS + "+"
    drawn = []
    for index, row in enumerate(rows):
        if index in GRAPHIC_ROWS:
            # The marks keep their colours; on a reversed row the cells
            # around them show reversed, the way the screen holds them.
            around = (
                (lambda c: f"\033[7m{c}\033[0m") if index in REVERSED
                else (lambda c: c)
            )
            drawn.append(
                "|" + "".join(PREVIEW.get(c) or around(c) for c in row) + "|"
            )
        elif index in REVERSED:
            drawn.append(f"|\033[7m{row}\033[0m|")
        else:
            drawn.append(f"|{row}|")
    return "\n".join([edge, *drawn, edge])
