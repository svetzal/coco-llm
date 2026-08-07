"""The game's rules, and the fact that the agent is not told them."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from rpsls import (
    MOVE_COUNT,
    MOVES,
    TIE,
    VERBS,
    FrequencyTable,
    RuleLearner,
    XorShift16,
    beats,
    describe,
    outcome,
)

DECISIVE = [(a, b) for a in range(MOVE_COUNT) for b in range(MOVE_COUNT) if beats(a, b)]


def test_every_move_beats_two_and_loses_to_two() -> None:
    for move in range(MOVE_COUNT):
        assert sum(beats(move, other) for other in range(MOVE_COUNT)) == 2
        assert sum(beats(other, move) for other in range(MOVE_COUNT)) == 2


def test_nothing_beats_itself() -> None:
    for move in range(MOVE_COUNT):
        assert not beats(move, move)
        assert outcome(move, move) == TIE


def test_the_narration_covers_exactly_the_decisive_pairs() -> None:
    """A pair described but impossible, or possible but silent, is a bug."""
    assert set(VERBS) == set(DECISIVE)
    assert len(DECISIVE) == 10
    for winner, loser in DECISIVE:
        assert describe(winner, loser).startswith(MOVES[winner])
        assert describe(winner, loser).endswith(MOVES[loser])


def test_a_tie_is_not_narrated() -> None:
    for move in range(MOVE_COUNT):
        assert describe(move, move) == ""


def test_the_canonical_phrasings_are_right() -> None:
    """Spot checks against the rules as they are actually spoken."""
    rock, spock, paper, lizard, scissors = range(MOVE_COUNT)
    assert describe(paper, rock) == "PAPER covers ROCK"
    assert describe(spock, rock) == "SPOCK vaporizes ROCK"
    assert describe(lizard, spock) == "LIZARD poisons SPOCK"
    assert describe(scissors, lizard) == "SCISSORS decapitates LIZARD"


def test_the_agent_is_never_handed_the_rules() -> None:
    """It starts knowing nothing and only learns cells it has played."""
    agent = RuleLearner(FrequencyTable(1, use_outcome=True), XorShift16(7))
    assert agent.known_cells() == 0
    agent.observe(0, 3)
    assert agent.known_cells() == 1
    agent.reset()
    assert agent.known_cells() == 0
