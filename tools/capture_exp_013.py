#!/usr/bin/env python3
"""Play RPSLS against the CoCo's agent, and record it.

EXP-008 passed its synthetic phase and then failed on real people. Every number
in EXP-013 so far is measured against six players invented by the same person
who wants the agent to win, so this is the step that decides whether any of it
survives. Nothing goes to the 6809 until a human has played it.

Two modes, because they answer different questions and only one of them is the
game:

  --blind   the opponent throws uniformly at random and nothing is predicted.
            Records unaided human tendency: are you readable when nobody is
            reading you? This is EXP-008's capture design, and it is the only
            session a *different* predictor can be honestly replayed against,
            because your moves did not depend on which predictor was watching.
  live      the real 100-byte agent plays, learning the rules and you at once.
            Records whether you stay readable while being read - the
            non-stationary target EXP-008 called its most interesting property.

The agent is not told the rules in either mode. It sees its own move, your
move, and what happened, exactly as you do.

It shows what it expects you to throw, *before* you throw it. That hands you
the way to beat it, which is the point: an opponent you can outwit once you
understand it is a demonstration, and one that only ever wins is a claim. `r`
empties both tables mid-session - EXP-008 required that key and called it the
falsifiability demonstration, because without it an audience cannot tell a
machine that learned from a difficulty curve that ramped.

Replaying a live session against a different predictor is counterfactual for
score: against a different opponent you would have thrown differently. It is
still honest for prediction accuracy given the same history, and that
distinction is why the blind mode exists.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from rpsls import (
    MOVE_COUNT,
    MOVES,
    TIE,
    WIN,
    FrequencyTable,
    RuleLearner,
    XorShift16,
    outcome,
)

DEFAULT_OUTPUT = ROOT / "experiments" / "data" / "EXP-013-captures.jsonl"
KEYS = "12345"
SCHEMA = "exp013-capture/1"


class BlindOpponent:
    """Throws at random and learns nothing. The control."""

    def __init__(self, random: XorShift16):
        self.random = random

    last_prediction = None

    def known_cells(self) -> int:
        return 0

    def reset(self) -> None:
        return

    def choose(self) -> int:
        return self.random.below(MOVE_COUNT)

    def observe(self, own: int, other: int) -> None:
        return


RESET = "reset"


def prompt(round_number: int, rounds: int) -> int | str | None:
    menu = "  ".join(f"{key}={name}" for key, name in zip(KEYS, MOVES, strict=True))
    while True:
        try:
            entry = input(f"[{round_number}/{rounds}] {menu}  (r resets, q quits) > ")
        except EOFError:
            return None
        entry = entry.strip()[:1].lower()
        if entry == "q":
            return None
        if entry == "r":
            return RESET
        if entry in KEYS:
            return KEYS.index(entry)
        print("  pick 1-5, r to wipe its memory, or q")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True, help="e.g. stacey-01")
    parser.add_argument("--rounds", type=int, default=60)
    parser.add_argument("--blind", action="store_true")
    parser.add_argument("--seed", type=lambda t: int(t, 0), default=0x1A2B)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()

    random = XorShift16(arguments.seed)
    if arguments.blind:
        agent = BlindOpponent(random)
        print("Blind session: the opponent throws at random and learns nothing.")
    else:
        agent = RuleLearner(FrequencyTable(1, use_outcome=True), random)
        print("The opponent starts knowing neither the rules nor you.")
    print(f"{arguments.rounds} rounds. Play however you like.\n")

    moves: list[int] = []
    thrown_by_agent: list[int] = []
    predictions: list[int] = []
    resets: list[int] = []
    score = 0.0
    index = 0
    while index < arguments.rounds:
        own = agent.choose()  # chosen before seeing the human's move
        if not arguments.blind:
            guess = agent.last_prediction
            expects = (
                f"it expects {MOVES[guess]}"
                if guess is not None and agent.has_expectation()
                else "it has no idea yet"
            )
            print(f"  {expects}   [{agent.known_cells()}/25 rules known]")
        human = prompt(index + 1, arguments.rounds)
        if human is None:
            break
        if human == RESET:
            agent.reset()
            resets.append(len(moves))
            print("  -- memory wiped. It knows nothing again. --\n")
            continue
        result = outcome(human, own)
        score += 1.0 if result == WIN else 0.5 if result == TIE else 0.0
        verdict = {WIN: "you win", TIE: "tie", 0: "you lose"}[result]
        print(f"      it threw {MOVES[own]:<9} {verdict}")
        moves.append(human)
        thrown_by_agent.append(own)
        predictions.append(agent.last_prediction if not arguments.blind else -1)
        agent.observe(own, human)
        index += 1

    if not moves:
        print("nothing recorded")
        return

    played = len(moves)
    record = {
        "schema": SCHEMA,
        "label": arguments.label,
        "recorded_utc": datetime.now(UTC).isoformat(),
        "mode": "blind" if arguments.blind else "live",
        "seed": arguments.seed,
        "moves": moves,
        "opponent": thrown_by_agent,
        "predicted": predictions,
        "resets_after_round": resets,
        "rules_known": agent.known_cells(),
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record) + "\n")

    print()
    print(
        f"{played} rounds. You scored {100.0 * score / played:.1f}% "
        f"(50% is a draw, so under 50 means it read you)."
    )
    if not arguments.blind:
        hits = sum(g == m for g, m in zip(predictions, moves, strict=True))
        print(
            f"It called your move {hits} times in {played} "
            f"({100.0 * hits / played:.0f}%, chance is 20%)."
        )
        print(f"It worked out {agent.known_cells()} of 25 rules from watching.")
        if resets:
            print(f"Memory wiped after rounds: {resets}")
    print(f"appended to {arguments.output}")


if __name__ == "__main__":
    main()
