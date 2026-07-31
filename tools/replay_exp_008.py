#!/usr/bin/env python3
"""Replay recorded human sessions through the EXP-008 predictors.

Runs captured move streams through exactly the candidate set the synthetic
sweep used, so the human numbers sit beside the synthetic ones on the same
scale. Reports each session separately, because a per-person result is the
honest unit here: one session is one person on one day, not "humans".
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from duel_arena import Capture, load_captures, move_names
from mimic_lm import (
    build_candidate_predictors,
    evaluate_stream,
    predictor_kind,
    predictor_storage_bytes,
)

DEFAULT_INPUT = ROOT / "experiments" / "data" / "EXP-008-captures.jsonl"
REQUIRED_MARGIN = 0.05


def report(
    capture: Capture,
    *,
    embeddings: list[int],
    shifts: list[int],
    window: int,
    seed: int,
) -> float:
    stream = capture.stream()
    predictors = build_candidate_predictors(
        embeddings=embeddings, shifts=shifts, seed=seed
    )
    results = evaluate_stream(stream, predictors, window=window)

    scored = min(window, len(stream))
    print(f"{capture.label}   {capture.recorded_utc}")
    print(
        f"  {capture.ticks} ticks across {len(capture.runs)} run(s), "
        f"scoring the final {scored}"
    )
    print(f"  {'method':<26}{'bytes':>8}{'window':>9}")

    best = {"table": None, "model": None, "uniform": None}
    for predictor, result in zip(predictors, results, strict=True):
        kind = predictor_kind(predictor)
        size = predictor_storage_bytes(predictor)
        print(
            f"  {result.name:<26}{size or '-':>8}{result.window_accuracy * 100:>8.1f}%"
        )
        if best[kind] is None or result.window_accuracy > best[kind].window_accuracy:
            best[kind] = result

    margin = best["model"].window_accuracy - best["table"].window_accuracy
    verdict = "model" if margin >= REQUIRED_MARGIN else "table"
    print(
        f"  -> best table {best['table'].window_accuracy * 100:.1f}%   "
        f"best model {best['model'].window_accuracy * 100:.1f}%   "
        f"margin {margin * 100:+.1f}pp   favours {verdict}"
    )
    print(f"  first 12 moves: {move_names(capture.runs[0][:12])}")
    print()
    return margin


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--label", type=str, default=None)
    parser.add_argument("--window", type=int, default=200)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--base-seed", type=int, default=6809)
    parser.add_argument("--embeddings", type=str, default="4,6,8")
    parser.add_argument("--learning-shifts", type=str, default="4")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    if not arguments.input.exists():
        print(f"no captures at {arguments.input}")
        print("record one first:")
        print("  make exp008-capture LABEL=stacey-01")
        return

    embeddings = [int(value) for value in arguments.embeddings.split(",")]
    shifts = [int(value) for value in arguments.learning_shifts.split(",")]
    captures = load_captures(arguments.input)
    if arguments.label:
        captures = [item for item in captures if item.label == arguments.label]
    if not captures:
        print("no captures matched")
        return

    print("EXP-008: recorded human sessions")
    print(
        f"scored window: final {arguments.window}   "
        f"model seeds: {arguments.seeds}   "
        f"learning shifts: {arguments.learning_shifts}"
    )
    print()

    margins: list[float] = []
    for capture in captures:
        for run in range(arguments.seeds):
            margin = report(
                capture,
                embeddings=embeddings,
                shifts=shifts,
                window=arguments.window,
                seed=arguments.base_seed + run * 101,
            )
            margins.append(margin)

    model_wins = sum(1 for margin in margins if margin >= REQUIRED_MARGIN)
    print("Summary")
    print(f"  sessions scored: {len(captures)}   runs: {len(margins)}")
    print(f"  mean margin: {sum(margins) / len(margins) * 100:+.1f}pp")
    print(
        f"  model clears {REQUIRED_MARGIN * 100:.0f}pp on {model_wins}/{len(margins)}"
    )
    if len(captures) < 3:
        print()
        print(
            "  Caution: fewer than three people recorded. This describes these "
            "sessions, not humans in general."
        )


if __name__ == "__main__":
    main()
