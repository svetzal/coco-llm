#!/usr/bin/env python3
"""Record a human dodging a chaser, for EXP-008.

Phase A left one blocking question: does a human move stream look like HABIT,
where a ninety-byte table wins, or like CIRCLE and FLEE, where the model wins
by roughly eight points? Synthetic players cannot answer it, because the same
person who wants the model to win wrote them.

This tool captures the real thing. Three properties are deliberate:

The capture is blind. No prediction is computed, drawn, or used to steer the
chaser. A visible ghost would record a human reacting to a predictor, when the
question is whether unaided human movement is predictable at all.

The keyboard is polled as held state at the tick rate, not consumed as events.
That is what the CoCo does when it scans its keyboard matrix, so the recorded
signal has the same shape as the signal the 6809 would eventually see.

Only moves are stored. Bearings and ranges are regenerated on replay by the
same deterministic arena the predictors were measured against, so the geometry
never forks into a second implementation.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

import pygame

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from duel_arena import (
    ARENA_HEIGHT,
    ARENA_WIDTH,
    DEFAULT_TICK_HZ,
    IDLE,
    MOVE_BY_DELTA,
    Arena,
    Capture,
    append_capture,
)

DEFAULT_OUTPUT = ROOT / "experiments" / "data" / "EXP-008-captures.jsonl"
CELL = 12
STATUS_HEIGHT = 56
CAUGHT_PAUSE_MS = 900

BACKGROUND = (16, 18, 20)
GRID = (30, 34, 38)
PLAYER_COLOUR = (120, 220, 140)
CHASER_COLOUR = (220, 90, 90)
TEXT = (210, 214, 218)
DIM = (120, 126, 132)


def load_font() -> pygame.font.Font | None:
    """Return a status font, or None if this build has no font module.

    pygame's font support is a compiled extension over SDL_ttf. A source build
    on a Python version with no published wheel can silently omit it, which is
    exactly what happened on Python 3.14 with upstream pygame 2.6.1. Losing the
    status text is a nuisance; losing the session is not acceptable, so the
    capture runs without text rather than refusing to start.
    """
    try:
        return pygame.font.SysFont("menlo,consolas,monospace", 14)
    except (NotImplementedError, ImportError, AttributeError, pygame.error):
        print("warning: no font module available; showing a progress bar instead")
        return None


def held_move(keys) -> int:
    """Quantize currently held direction keys to one move token."""
    right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
    left = keys[pygame.K_LEFT] or keys[pygame.K_a]
    down = keys[pygame.K_DOWN] or keys[pygame.K_s]
    up = keys[pygame.K_UP] or keys[pygame.K_w]
    return MOVE_BY_DELTA[(int(right) - int(left), int(down) - int(up))]


def draw(
    surface: pygame.Surface,
    font: pygame.font.Font | None,
    arena: Arena,
    *,
    captured: int,
    target: int,
    runs: int,
    run_ticks: int,
    caught: bool,
) -> None:
    surface.fill(BACKGROUND)
    for x in range(0, ARENA_WIDTH * CELL, CELL):
        pygame.draw.line(surface, GRID, (x, 0), (x, ARENA_HEIGHT * CELL))
    for y in range(0, ARENA_HEIGHT * CELL + 1, CELL):
        pygame.draw.line(surface, GRID, (0, y), (ARENA_WIDTH * CELL, y))

    for colour, (cell_x, cell_y) in (
        (CHASER_COLOUR, (arena.opponent_x, arena.opponent_y)),
        (PLAYER_COLOUR, (arena.player_x, arena.player_y)),
    ):
        pygame.draw.rect(
            surface,
            colour,
            pygame.Rect(cell_x * CELL, cell_y * CELL, CELL, CELL),
        )

    base = ARENA_HEIGHT * CELL + 10
    if font is None:
        width = ARENA_WIDTH * CELL - 20
        filled = int(width * captured / max(1, target))
        pygame.draw.rect(surface, GRID, pygame.Rect(10, base, width, 10))
        pygame.draw.rect(
            surface,
            CHASER_COLOUR if caught else PLAYER_COLOUR,
            pygame.Rect(10, base, filled, 10),
        )
        pygame.display.flip()
        return

    progress = (
        f"captured {captured}/{target} ticks   runs {runs}   this run {run_ticks}"
    )
    surface.blit(font.render(progress, True, TEXT), (10, base))
    hint = "CAUGHT" if caught else "arrows or WASD to move   Esc to stop early"
    surface.blit(
        font.render(hint, True, CHASER_COLOUR if caught else DIM), (10, base + 22)
    )
    pygame.display.flip()


def run_session(*, label: str, target_ticks: int, tick_hz: int) -> Capture | None:
    pygame.init()
    surface = pygame.display.set_mode(
        (ARENA_WIDTH * CELL, ARENA_HEIGHT * CELL + STATUS_HEIGHT)
    )
    pygame.display.set_caption(f"EXP-008 capture: {label}")
    font = load_font()
    clock = pygame.time.Clock()

    arena = Arena()
    runs: list[tuple[int, ...]] = []
    outcomes: list[str] = []
    current: list[int] = []
    captured = 0
    accumulated = 0.0
    step = 1000.0 / tick_hz
    caught_until = 0
    stopped = False
    failed = False

    # Anything already played is real data. A crash partway through must not
    # cost the whole session, so the loop hands back whatever it has.
    try:
        while captured < target_ticks and not stopped:
            elapsed = clock.tick(60)
            now = pygame.time.get_ticks()

            for event in pygame.event.get():
                quitting = event.type == pygame.QUIT
                escaping = event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                if quitting or escaping:
                    stopped = True

            if now >= caught_until:
                accumulated += elapsed
                while accumulated >= step and captured < target_ticks:
                    accumulated -= step
                    move = held_move(pygame.key.get_pressed())
                    current.append(move)
                    captured += 1
                    arena.apply(move)

                    if arena.is_caught():
                        runs.append(tuple(current))
                        outcomes.append("caught")
                        current = []
                        arena = Arena()
                        caught_until = now + CAUGHT_PAUSE_MS
                        accumulated = 0.0
                        break

            draw(
                surface,
                font,
                arena,
                captured=captured,
                target=target_ticks,
                runs=len(runs),
                run_ticks=len(current),
                caught=now < caught_until,
            )
    except Exception as error:  # noqa: BLE001 - keep the data, report the cause
        failed = True
        print(f"capture interrupted: {type(error).__name__}: {error}")
        print("keeping the ticks recorded so far")
    finally:
        pygame.quit()

    if current:
        runs.append(tuple(current))
        outcomes.append(
            "interrupted" if failed else "stopped" if stopped else "expired"
        )
    if not runs:
        return None

    return Capture(
        label=label,
        recorded_utc=datetime.now(UTC).isoformat(timespec="seconds"),
        tick_hz=tick_hz,
        runs=tuple(runs),
        outcomes=tuple(outcomes),
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True, help="who is playing, e.g. stacey-01")
    parser.add_argument("--ticks", type=int, default=1800)
    parser.add_argument("--tick-hz", type=int, default=DEFAULT_TICK_HZ)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    seconds = arguments.ticks / arguments.tick_hz
    print(f"EXP-008 capture: {arguments.label}")
    print(f"target {arguments.ticks} ticks at {arguments.tick_hz} Hz (~{seconds:.0f}s)")
    print("no prediction is shown or used; the chaser is not adaptive")
    print()

    capture = run_session(
        label=arguments.label,
        target_ticks=arguments.ticks,
        tick_hz=arguments.tick_hz,
    )
    if capture is None:
        print("nothing captured")
        return

    append_capture(arguments.output, capture)
    idle = sum(run.count(IDLE) for run in capture.runs)
    print(f"captured {capture.ticks} ticks across {len(capture.runs)} run(s)")
    print(f"idle ticks: {idle} ({idle / capture.ticks * 100:.1f}%)")
    print(f"appended to {arguments.output}")


if __name__ == "__main__":
    main()
