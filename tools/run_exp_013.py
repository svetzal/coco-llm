#!/usr/bin/env python3
"""Which predictor should drive the RPSLS opponent?

EXP-008's null result says a small frequency table is the thing to beat, so
this measures the tables against each other and against synthetic players
first. Nothing neural is built until a table has been shown to leave something
on the table, and nothing is built for the CoCo until a human has been
recorded - EXP-008's synthetic phase passed on players its human phase then
failed on.

Two numbers per pairing:

  accuracy  how often the predictor named the player's next move. This is what
            EXP-008 measured, and it is comparable across players.
  score     the opponent's actual round win rate, counting a tie as a half.
            This is what a person in the room feels, and it is not the same
            number: a predictor can be right often and still be countered.

The synthetic players are declared here rather than discovered, so that a
predictor tuned until it wins is visibly tuned against a known set.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from rpsls import (
    LOSS,
    MOVE_COUNT,
    MOVES,
    TIE,
    Backoff,
    FrequencyTable,
    Uniform,
    XorShift16,
    counter,
    outcome,
)


class Player:
    def __init__(self, name: str, random: XorShift16):
        self.name = name
        self.random = random
        self.history: list[int] = []
        self.last_outcome = TIE

    def move(self) -> int:
        raise NotImplementedError

    def observe(self, own: int, other: int) -> None:
        self.history.append(own)
        self.last_outcome = outcome(own, other)


class Random(Player):
    def move(self) -> int:
        return self.random.below(MOVE_COUNT)


class Cycle(Player):
    """Walks the moves in order. The easiest structure there is."""

    def move(self) -> int:
        return len(self.history) % MOVE_COUNT


class Favourite(Player):
    """Throws one move 60% of the time. The commonest beginner habit."""

    def move(self) -> int:
        return 0 if self.random.below(5) < 3 else self.random.below(MOVE_COUNT)


class WinStayLoseShift(Player):
    """Repeats after a win, changes after a loss. Documented in real play."""

    def move(self) -> int:
        if not self.history:
            return self.random.below(MOVE_COUNT)
        if self.last_outcome == LOSS:
            return counter(self.history[-1])
        return self.history[-1]


class NeverRepeat(Player):
    """Avoids the move just thrown - people randomize by not repeating."""

    def move(self) -> int:
        if not self.history:
            return self.random.below(MOVE_COUNT)
        choice = self.random.below(MOVE_COUNT - 1)
        return choice if choice < self.history[-1] else choice + 1


class Reactive(Player):
    """Throws what would have beaten the opponent's last move.

    The only player here whose behaviour depends on the opponent, so it is the
    one that can turn the prediction loop into a chase.
    """

    def __init__(self, name: str, random: XorShift16):
        super().__init__(name, random)
        self.other_last: int | None = None

    def move(self) -> int:
        if self.other_last is None:
            return self.random.below(MOVE_COUNT)
        return counter(self.other_last)

    def observe(self, own: int, other: int) -> None:
        super().observe(own, other)
        self.other_last = other


PLAYERS = (
    ("random", Random),
    ("cycle", Cycle),
    ("favourite", Favourite),
    ("win-stay", WinStayLoseShift),
    ("never-repeat", NeverRepeat),
    ("reactive", Reactive),
)


def predictors(random: XorShift16):
    return [
        Uniform(random),
        FrequencyTable(order=0),
        FrequencyTable(order=1),
        FrequencyTable(order=2),
        FrequencyTable(order=1, use_outcome=True),
        Backoff(),
        Backoff(use_outcome=True),
    ]


# The player's generator must not be the predictor's. Seeded alike, a uniform
# predictor drew the identical stream and "predicted" a random player at 100%.
PLAYER_SEED_OFFSET = 0x5A5A


def play(player_class, predictor, rounds: int, seed: int) -> tuple[float, float]:
    player = player_class("player", XorShift16(seed ^ PLAYER_SEED_OFFSET))
    hits, score = 0, 0.0
    for _ in range(rounds):
        guess = predictor.predict()
        opponent = counter(guess)
        thrown = player.move()
        hits += guess == thrown
        result = outcome(opponent, thrown)
        score += 1.0 if result == 2 else 0.5 if result == TIE else 0.0
        player.observe(thrown, opponent)
        predictor.observe(thrown, opponent)
    return 100.0 * hits / rounds, 100.0 * score / rounds


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=300)
    parser.add_argument("--seed", type=lambda t: int(t, 0), default=0x1A2B)
    arguments = parser.parse_args()

    names = [p.name for p in predictors(XorShift16(1))]
    sizes = [p.table_bytes for p in predictors(XorShift16(1))]

    print(f"{arguments.rounds} rounds per pairing, {len(MOVES)} moves")
    print("chance accuracy 20.0%, chance score 50.0%")
    print()
    print(f"  {'':<14}" + "".join(f"{name:>16}" for name in names))
    print(f"  {'bytes':<14}" + "".join(f"{size:>16}" for size in sizes))
    print()

    totals = [0.0] * len(names)
    for label, player_class in PLAYERS:
        row = []
        for index, predictor in enumerate(predictors(XorShift16(arguments.seed))):
            accuracy, score = play(
                player_class, predictor, arguments.rounds, arguments.seed
            )
            totals[index] += score
            row.append(f"{accuracy:>7.1f}/{score:<8.1f}")
        print(f"  {label:<14}" + "".join(f"{cell:>16}" for cell in row))

    print()
    print(
        f"  {'mean score':<14}" + "".join(f"{t / len(PLAYERS):>15.1f}%" for t in totals)
    )
    print()
    print("cells read accuracy/score. Score is what a person feels; 50% is a")
    print("draw. A predictor that cannot beat 50% on 'random' is behaving.")


if __name__ == "__main__":
    main()
