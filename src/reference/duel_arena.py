"""Arena, token encoding, and synthetic players for EXP-008.

The adaptive-opponent experiment turns a player's movement into a token stream
and asks a next-token model to predict it. This module supplies the stream. It
holds no model code so that the prediction methods under comparison can be
swapped without touching the environment that generates their data.

Arena coordinates are abstract grid units matching a 64 x 32 semigraphics-4
display. Bearing and range are computed in those raw units. Real SG4 blocks are
taller than they are wide, so a Phase C implementation must decide whether to
correct for aspect ratio. Phase A deliberately does not, because the model
learns whatever consistent geometry it is given and inventing a correction now
would add precision the experiment has not earned.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from fixed_token_lm import XorShift16

MOVE_TOKENS = ("IDLE", "N", "NE", "E", "SE", "S", "SW", "W", "NW")
BEARING_TOKENS = ("B0", "B1", "B2", "B3", "B4", "B5", "B6", "B7")
RANGE_TOKENS = ("NEAR", "MID", "FAR")

IDLE = 0
MOVE_COUNT = len(MOVE_TOKENS)
BEARING_BASE = MOVE_COUNT
RANGE_BASE = BEARING_BASE + len(BEARING_TOKENS)
SITUATIONAL_VOCABULARY = RANGE_BASE + len(RANGE_TOKENS)

HISTORY_LAYOUT = "history"
SITUATIONAL_LAYOUT = "situational"
LAYOUTS = (HISTORY_LAYOUT, SITUATIONAL_LAYOUT)

CONTEXT_SIZE = 5
ARENA_WIDTH = 64
ARENA_HEIGHT = 32
NEAR_LIMIT = 6
MID_LIMIT = 16

# Compass moves in clockwise order starting at N, matching MOVE_TOKENS[1:].
MOVE_DELTAS = (
    (0, 0),
    (0, -1),
    (1, -1),
    (1, 0),
    (1, 1),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (-1, -1),
)
MOVE_BY_DELTA = {delta: index for index, delta in enumerate(MOVE_DELTAS)}


def rotate_move(move: int, steps: int) -> int:
    """Rotate a compass move clockwise by `steps` eighths of a turn."""
    if move == IDLE:
        return IDLE
    return ((move - 1 + steps) % 8) + 1


def direction_index(delta_x: int, delta_y: int) -> int:
    """Quantize a vector to one of eight compass moves, or IDLE when zero.

    The 2:1 ratio test approximates a 22.5 degree octant boundary using only
    comparisons and a shift, so the same rule ports to the 6809 without
    trigonometry.
    """
    if delta_x == 0 and delta_y == 0:
        return IDLE

    span_x = abs(delta_x)
    span_y = abs(delta_y)
    if span_y * 2 < span_x:
        step_x = 1 if delta_x > 0 else -1
        step_y = 0
    elif span_x * 2 < span_y:
        step_x = 0
        step_y = 1 if delta_y > 0 else -1
    else:
        step_x = 1 if delta_x > 0 else -1
        step_y = 1 if delta_y > 0 else -1

    return MOVE_BY_DELTA[(step_x, step_y)]


def range_bucket(delta_x: int, delta_y: int) -> int:
    """Bucket Chebyshev distance into NEAR, MID, or FAR."""
    distance = max(abs(delta_x), abs(delta_y))
    if distance <= NEAR_LIMIT:
        return 0
    if distance <= MID_LIMIT:
        return 1
    return 2


@dataclass(frozen=True)
class TickRecord:
    """Everything a predictor may look at before the player's move is known."""

    history: tuple[int, ...]
    bearing: int
    range_index: int

    def context(self, layout: str) -> tuple[int, ...]:
        """Build the five-position model context for the requested layout."""
        if layout == HISTORY_LAYOUT:
            return self.history[-CONTEXT_SIZE:]
        if layout == SITUATIONAL_LAYOUT:
            return (
                BEARING_BASE + self.bearing,
                RANGE_BASE + self.range_index,
                *self.history[-3:],
            )
        raise ValueError(f"unknown layout: {layout}")


def input_vocabulary_size(layout: str) -> int:
    if layout == HISTORY_LAYOUT:
        return MOVE_COUNT
    if layout == SITUATIONAL_LAYOUT:
        return SITUATIONAL_VOCABULARY
    raise ValueError(f"unknown layout: {layout}")


class Arena:
    """A bounded grid holding a player and a chasing opponent.

    The opponent does not use the model. Phase A measures prediction quality
    against a fixed chaser so that the target stays stationary; closing the
    loop, where the player adapts because the opponent adapts, is deliberately
    left to Phase C.
    """

    def __init__(
        self,
        *,
        player: tuple[int, int] = (16, 16),
        opponent: tuple[int, int] = (48, 16),
    ):
        self.player_x, self.player_y = player
        self.opponent_x, self.opponent_y = opponent
        self.history: list[int] = [IDLE] * CONTEXT_SIZE
        self.ticks = 0

    @property
    def delta(self) -> tuple[int, int]:
        return self.opponent_x - self.player_x, self.opponent_y - self.player_y

    def record(self) -> TickRecord:
        delta_x, delta_y = self.delta
        bearing = direction_index(delta_x, delta_y)
        return TickRecord(
            history=tuple(self.history),
            bearing=max(0, bearing - 1),
            range_index=range_bucket(delta_x, delta_y),
        )

    def apply(self, move: int) -> None:
        """Advance one tick: the player moves, then the opponent chases."""
        step_x, step_y = MOVE_DELTAS[move]
        self.player_x = max(0, min(ARENA_WIDTH - 1, self.player_x + step_x))
        self.player_y = max(0, min(ARENA_HEIGHT - 1, self.player_y + step_y))
        self.history = self.history[1:] + [move]
        self.ticks += 1

        # The chaser moves at half speed so the duel is survivable, and stops
        # adjacent so that bearing never becomes degenerate.
        if self.ticks % 2 == 0:
            delta_x, delta_y = self.delta
            if max(abs(delta_x), abs(delta_y)) > 1:
                toward = direction_index(-delta_x, -delta_y)
                chase_x, chase_y = MOVE_DELTAS[toward]
                self.opponent_x += chase_x
                self.opponent_y += chase_y


class SyntheticPlayer:
    """A seeded, scripted movement policy.

    Every policy returns the player's *intended* move. When the arena clamps
    that move at a wall the position does not change, but the token still
    records the intent, because intent is what the model is asked to predict.
    """

    name = "BASE"

    def __init__(self, seed: int):
        self.random = XorShift16(seed)
        self.last_move = IDLE

    def choose(self, record: TickRecord) -> int:
        raise NotImplementedError

    def move(self, record: TickRecord) -> int:
        self.last_move = self.choose(record)
        return self.last_move

    def _uniform_move(self) -> int:
        return self.random.next() % MOVE_COUNT

    def _chance(self, percent: int) -> bool:
        return self.random.next() % 100 < percent


class RandomPlayer(SyntheticPlayer):
    """Negative control. No method should beat the uniform baseline here."""

    name = "RANDOM"

    def choose(self, record: TickRecord) -> int:
        return self._uniform_move()


class ZigzagPlayer(SyntheticPlayer):
    """A fixed repeating pattern with noise. A bigram table should do well."""

    name = "ZIGZAG"
    PATTERN = (3, 3, 2, 1, 1, 8, 7, 7, 6, 5, 5, 4)

    def __init__(self, seed: int):
        super().__init__(seed)
        self.step = 0

    def choose(self, record: TickRecord) -> int:
        move = self.PATTERN[self.step % len(self.PATTERN)]
        self.step += 1
        if self._chance(10):
            return self._uniform_move()
        return move


class CirclePlayer(SyntheticPlayer):
    """Strafes perpendicular to the opponent. Needs bearing to predict."""

    name = "CIRCLE"

    def choose(self, record: TickRecord) -> int:
        if self._chance(10):
            return self._uniform_move()
        return rotate_move(record.bearing + 1, 2)


class FleePlayer(SyntheticPlayer):
    """Moves directly away. A pure function of bearing."""

    name = "FLEE"

    def choose(self, record: TickRecord) -> int:
        if self._chance(10):
            return self._uniform_move()
        return rotate_move(record.bearing + 1, 4)


class PanicPlayer(SyntheticPlayer):
    """Flees when NEAR, wanders otherwise. Needs bearing and range together."""

    name = "PANIC"

    def choose(self, record: TickRecord) -> int:
        if record.range_index == 0:
            if self._chance(10):
                return self._uniform_move()
            return rotate_move(record.bearing + 1, 4)
        if self._chance(60) and self.last_move != IDLE:
            return self.last_move
        return self._uniform_move()


class HabitPlayer(SyntheticPlayer):
    """Momentum, occasional turns, and a bias away when the opponent is close.

    This is the closest available proxy for a human and the least favourable
    to any single method, because it mixes history-driven and situation-driven
    behaviour.
    """

    name = "HABIT"

    def choose(self, record: TickRecord) -> int:
        if record.range_index == 0 and self._chance(40):
            return rotate_move(record.bearing + 1, 4)
        if self.last_move != IDLE and self._chance(70):
            return self.last_move
        if self.last_move != IDLE and self._chance(67):
            return rotate_move(self.last_move, 1 if self._chance(50) else -1)
        return self._uniform_move()


PLAYER_TYPES: tuple[type[SyntheticPlayer], ...] = (
    RandomPlayer,
    ZigzagPlayer,
    CirclePlayer,
    FleePlayer,
    PanicPlayer,
    HabitPlayer,
)
PLAYER_BY_NAME = {player.name: player for player in PLAYER_TYPES}


def generate_stream(
    player_type: type[SyntheticPlayer],
    *,
    ticks: int,
    seed: int,
) -> list[tuple[TickRecord, int]]:
    """Produce a deterministic sequence of (situation, chosen move) pairs."""
    arena = Arena()
    player = player_type(seed)
    stream: list[tuple[TickRecord, int]] = []

    for _ in range(ticks):
        record = arena.record()
        move = player.move(record)
        stream.append((record, move))
        arena.apply(move)

    return stream


def move_names(moves: Sequence[int]) -> str:
    return " ".join(MOVE_TOKENS[move] for move in moves)
