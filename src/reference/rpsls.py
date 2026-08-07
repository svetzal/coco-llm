"""Rock Paper Scissors Lizard Spock, and the predictors that might learn a human.

EXP-008 already asked whether a neural model can learn a live player's move
stream on this machine, and closed as not supported: a ninety-byte order-1
frequency table predicted better than every neural candidate, on all three
recorded human sessions. That result is about predicting a human's next
discrete move, which is exactly what this game needs, so the table is the
thing to beat here rather than the thing to improve on.

What is genuinely different about RPSLS, and worth testing before assuming the
old answer transfers:

  the target fights back  A player who notices they are being read will try to
                          stop being readable. EXP-008's players were moving
                          through an arena; these are choosing against an
                          opponent that is choosing against them.
  outcome matters         Human play in this family is documented to depend on
                          whether the last round was won or lost - win-stay,
                          lose-shift - not only on what was thrown. That is a
                          context-design question, and EXP-008's secondary
                          hypothesis was precisely that situational context
                          beats history-only context when behaviour depends on
                          the situation.
  no cycle pressure       The game is turn-based, so the model no longer shares
                          a budget with a real-time loop. One of EXP-008's four
                          breaking properties does not apply.

Moves are ordered so that the rules become arithmetic: a beats b exactly when
(a - b) mod 5 is 1 or 2. On a 6809 that is a subtract and two compares, which
matters because the counter to a predicted move is (p + 1) mod 5.
"""

from __future__ import annotations

from collections.abc import Sequence

MOVES = ("ROCK", "SPOCK", "PAPER", "LIZARD", "SCISSORS")
MOVE_COUNT = len(MOVES)
LOSS, TIE, WIN = 0, 1, 2
OUTCOMES = 3


def beats(first: int, second: int) -> bool:
    """Rock crushes Scissors and Lizard; Spock vaporizes Rock and smashes
    Scissors; and so on for all ten pairs."""
    return (first - second) % MOVE_COUNT in (1, 2)


# What the game says happened, for each of the ten decisive pairs. This is the
# *game's* knowledge, not the agent's: the agent is told only win, tie or loss
# and never sees these. Keeping that straight matters, because the whole point
# of the demo is that the machine works the rules out while the game narrates
# them to the person.
VERBS = {
    (0, 4): "crushes",  # ROCK / SCISSORS
    (0, 3): "crushes",  # ROCK / LIZARD
    (2, 0): "covers",  # PAPER / ROCK
    (2, 1): "disproves",  # PAPER / SPOCK
    (4, 2): "cuts",  # SCISSORS / PAPER
    (4, 3): "decapitates",  # SCISSORS / LIZARD
    (3, 2): "eats",  # LIZARD / PAPER
    (3, 1): "poisons",  # LIZARD / SPOCK
    (1, 4): "smashes",  # SPOCK / SCISSORS
    (1, 0): "vaporizes",  # SPOCK / ROCK
}


def describe(winner: int, loser: int) -> str:
    """ "PAPER covers ROCK". Empty for a tie, which needs no explaining."""
    verb = VERBS.get((winner, loser))
    return "" if verb is None else f"{MOVES[winner]} {verb} {MOVES[loser]}"


def outcome(player: int, opponent: int) -> int:
    if player == opponent:
        return TIE
    return WIN if beats(player, opponent) else LOSS


def counter(move: int) -> int:
    """A move that beats the given one. Two exist; this takes the nearer."""
    return (move + 1) % MOVE_COUNT


class XorShift16:
    """The same generator the CoCo runs, so a replay is a replay."""

    def __init__(self, seed: int):
        self.state = seed & 0xFFFF or 1

    def next(self) -> int:
        value = self.state
        value ^= (value << 7) & 0xFFFF
        value ^= value >> 9
        value ^= (value << 8) & 0xFFFF
        self.state = value & 0xFFFF
        return self.state

    def below(self, count: int) -> int:
        mask = 1
        while mask < count:
            mask = mask * 2 + 1
        for _ in range(16):
            candidate = self.next() & mask
            if candidate < count:
                return candidate
        return count - 1


class Predictor:
    """Predicts the player's next move. `observe` is called after each round."""

    name = "predictor"
    table_bytes = 0

    def predict(self) -> int:
        raise NotImplementedError

    def observe(self, player: int, opponent: int) -> None:
        raise NotImplementedError


class Uniform(Predictor):
    """The floor. Unbeatable in expectation and beats nothing."""

    name = "uniform"

    def __init__(self, random: XorShift16):
        self.random = random

    def predict(self) -> int:
        return self.random.below(MOVE_COUNT)

    def observe(self, player: int, opponent: int) -> None:
        return


class FrequencyTable(Predictor):
    """Counts of the player's next move, conditioned on a context.

    `order` is how many of the player's own previous moves the context holds;
    `use_outcome` adds the result of the previous round to it. Counts are
    bytes and halve when any reaches 255, which is both how the CoCo would
    hold them and how the table forgets a player who changes their mind.
    """

    def __init__(self, order: int = 1, use_outcome: bool = False):
        self.order = order
        self.use_outcome = use_outcome
        self.contexts = MOVE_COUNT**order * (OUTCOMES if use_outcome else 1)
        self.counts = [[0] * MOVE_COUNT for _ in range(self.contexts)]
        self.history: list[int] = []
        self.last_outcome = TIE
        self.name = f"order-{order}" + ("+outcome" if use_outcome else "")
        self.table_bytes = self.contexts * MOVE_COUNT

    def context(self) -> int | None:
        if len(self.history) < self.order:
            return None
        index = 0
        for move in self.history[len(self.history) - self.order :]:
            index = index * MOVE_COUNT + move
        if self.use_outcome:
            index = index * OUTCOMES + self.last_outcome
        return index

    def has_evidence(self) -> bool:
        """Whether the current context has been seen at all.

        predict() falls back to move 0 when it has nothing, which is a default
        and not a guess. Displaying it as "it expects ROCK" would show an
        audience confidence the table does not have.
        """
        index = self.context()
        return index is not None and any(self.counts[index])

    def predict(self) -> int:
        index = self.context()
        if index is None:
            return 0
        row = self.counts[index]
        best = max(row)
        return 0 if best == 0 else row.index(best)

    def observe(self, player: int, opponent: int) -> None:
        index = self.context()
        if index is not None:
            row = self.counts[index]
            row[player] += 1
            if row[player] > 255:
                for move in range(MOVE_COUNT):
                    row[move] //= 2
        self.history.append(player)
        self.last_outcome = outcome(player, opponent)


class Backoff(Predictor):
    """Longest context with any evidence wins, falling back to shorter ones.

    EXP-008 found the model beat an order-2 table with backoff on one
    structured player, so this is carried forward as the strongest table.
    """

    name = "backoff"

    def __init__(self, orders: Sequence[int] = (2, 1, 0), use_outcome: bool = False):
        self.tables = [FrequencyTable(order, use_outcome) for order in orders]
        self.name = "backoff" + ("+outcome" if use_outcome else "")
        self.table_bytes = sum(table.table_bytes for table in self.tables)

    def predict(self) -> int:
        for table in self.tables:
            index = table.context()
            if index is not None and any(table.counts[index]):
                return table.predict()
        return 0

    def observe(self, player: int, opponent: int) -> None:
        for table in self.tables:
            table.observe(player, opponent)


UNKNOWN, KNOWN_LOSS, KNOWN_TIE, KNOWN_WIN = 0, 1, 2, 3


class RuleLearner:
    """Plays without being told which move beats which.

    Every predictor above is handed `counter()` - it guesses the player's move
    and plays the known answer. That is a machine that has read the rules. A
    person sitting down to Rock Paper Scissors Lizard Spock for the first time
    has not, and finds out the same way this does: throw something, see what
    happened, remember it.

    So two things are learned at once, and they behave completely differently:

      the rules      25 cells, deterministic, stationary. One cell is revealed
                     per round and never changes afterwards. This is learnable
                     to certainty, and the only question is how fast.
      the opponent   non-stationary and adversarial, exactly as before.

    Until a cell is known there is nothing to exploit, so early play is
    exploration whether or not it is chosen: a move whose outcome against the
    predicted throw has never been seen is worth more than a move known to tie.

    `symmetric` is a prior, not an observation. Seeing that ROCK beats SCISSORS
    tells a person that SCISSORS loses to ROCK; a table of independent cells has
    to be told that twice. It halves what must be seen, and it is an assumption
    about the game rather than a fact read off it, so it is measured separately.
    """

    def __init__(self, opponent, random: XorShift16, symmetric: bool = False):
        self.rules = [[UNKNOWN] * MOVE_COUNT for _ in range(MOVE_COUNT)]
        self.opponent = opponent
        self.random = random
        self.symmetric = symmetric
        # What it expected the player to throw, so the guess can be shown
        # before the throw rather than justified after it.
        self.last_prediction: int | None = None

    def reset(self) -> None:
        """Forget everything: the rules and the player.

        EXP-008 required this and called it the falsifiability demonstration
        rather than a convenience. Without it an audience cannot tell a model
        that learned from a difficulty curve that ramped - press it, and the
        prediction goes wrong in front of them and has to climb back.
        """
        self.rules = [[UNKNOWN] * MOVE_COUNT for _ in range(MOVE_COUNT)]
        self.opponent = type(self.opponent)(
            self.opponent.order, self.opponent.use_outcome
        )
        self.last_prediction = None

    @property
    def table_bytes(self) -> int:
        return MOVE_COUNT * MOVE_COUNT + self.opponent.table_bytes

    def known_cells(self) -> int:
        return sum(cell != UNKNOWN for row in self.rules for cell in row)

    def has_expectation(self) -> bool:
        return self.opponent.has_evidence()

    def choose(self) -> int:
        """Best against the predicted throw; an unseen cell beats a known tie."""
        predicted = self.opponent.predict()
        self.last_prediction = predicted
        column = [self.rules[move][predicted] for move in range(MOVE_COUNT)]

        wins = [m for m in range(MOVE_COUNT) if column[m] == KNOWN_WIN]
        if wins:
            return wins[self.random.below(len(wins))]
        unseen = [m for m in range(MOVE_COUNT) if column[m] == UNKNOWN]
        if unseen:
            return unseen[self.random.below(len(unseen))]
        ties = [m for m in range(MOVE_COUNT) if column[m] == KNOWN_TIE]
        if ties:
            return ties[self.random.below(len(ties))]
        return self.random.below(MOVE_COUNT)

    def observe(self, own: int, other: int) -> None:
        result = outcome(own, other)
        self.rules[own][other] = KNOWN_LOSS + result
        if self.symmetric:
            mirror = {KNOWN_WIN: KNOWN_LOSS, KNOWN_LOSS: KNOWN_WIN}
            self.rules[other][own] = mirror.get(
                KNOWN_LOSS + result, KNOWN_LOSS + result
            )
        self.opponent.observe(other, own)


class RulesKnown:
    """The EXP-013 opponent: predict, then play the counter it was given."""

    def __init__(self, opponent):
        self.opponent = opponent
        self.table_bytes = opponent.table_bytes
        self.last_prediction: int | None = None

    def known_cells(self) -> int:
        return MOVE_COUNT * MOVE_COUNT

    def choose(self) -> int:
        self.last_prediction = self.opponent.predict()
        return counter(self.last_prediction)

    def observe(self, own: int, other: int) -> None:
        self.opponent.observe(other, own)
