"""EXP-008 Phase A sweep: does the model beat a memory-matched table?

Runs every synthetic player against the table baselines and against both
context layouts at several embedding widths, scoring prequentially. Prints the
per-player detail, then evaluates the declared Phase A gates.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from duel_arena import (
    HISTORY_LAYOUT,
    PLAYER_TYPES,
    SITUATIONAL_LAYOUT,
    SyntheticPlayer,
    generate_stream,
)
from mimic_lm import (
    MarginalBaseline,
    MimicConfig,
    MimicPredictor,
    TableBaseline,
    UniformBaseline,
    evaluate_stream,
)

PARAMETER_CEILING = 1024
NOISE_MARGIN = 0.02
REQUIRED_MARGIN = 0.05
REQUIRED_WINS = 3


@dataclass
class MethodSummary:
    name: str
    kind: str
    storage_bytes: int
    window_accuracy: float


def build_predictors(embeddings: list[int], shifts: list[int], seed: int) -> list:
    predictors = [
        UniformBaseline(seed=seed),
        MarginalBaseline(),
        TableBaseline(1),
        TableBaseline(2),
    ]
    for layout in (HISTORY_LAYOUT, SITUATIONAL_LAYOUT):
        for embedding in embeddings:
            for shift in shifts:
                predictors.append(
                    MimicPredictor(
                        MimicConfig(
                            layout=layout,
                            embedding=embedding,
                            seed=seed,
                            learning_shift=shift,
                        )
                    )
                )
    return predictors


def storage_bytes(predictor) -> int:
    if isinstance(predictor, MimicPredictor):
        return predictor.model.master_bytes
    if isinstance(predictor, TableBaseline):
        return predictor.counter_cells
    if isinstance(predictor, MarginalBaseline):
        return 9
    return 0


def kind_of(predictor) -> str:
    if isinstance(predictor, MimicPredictor):
        return "model"
    if isinstance(predictor, UniformBaseline):
        return "uniform"
    return "table"


def run_player(
    player_type: type[SyntheticPlayer],
    *,
    embeddings: list[int],
    shifts: list[int],
    ticks: int,
    window: int,
    seeds: int,
    base_seed: int,
) -> tuple[list[MethodSummary], int, tuple[int, int]]:
    totals: dict[str, float] = {}
    order: list[tuple[str, str, int]] = []
    magnitude = 0
    score_low = 0
    score_high = 0

    for run in range(seeds):
        seed = base_seed + run * 101
        stream = generate_stream(player_type, ticks=ticks, seed=seed)
        predictors = build_predictors(embeddings, shifts, seed)
        results = evaluate_stream(stream, predictors, window=window)

        for predictor, result in zip(predictors, results, strict=True):
            totals[result.name] = totals.get(result.name, 0.0) + result.window_accuracy
            if run == 0:
                order.append(
                    (result.name, kind_of(predictor), storage_bytes(predictor))
                )
            if isinstance(predictor, MimicPredictor):
                magnitude = max(magnitude, predictor.model.max_context_magnitude)
                score_low = min(score_low, predictor.model.minimum_score)
                score_high = max(score_high, predictor.model.maximum_score)

    summaries = [
        MethodSummary(
            name=name,
            kind=kind,
            storage_bytes=size,
            window_accuracy=totals[name] / seeds,
        )
        for name, kind, size in order
    ]
    return summaries, magnitude, (score_low, score_high)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticks", type=int, default=600)
    parser.add_argument("--window", type=int, default=200)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--base-seed", type=int, default=6809)
    parser.add_argument("--embeddings", type=str, default="4,6,8")
    parser.add_argument("--learning-shifts", type=str, default="4")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    embeddings = [int(value) for value in arguments.embeddings.split(",")]
    shifts = [int(value) for value in arguments.learning_shifts.split(",")]

    print("EXP-008 Phase A: adaptive opponent sweep")
    print(
        f"ticks per run: {arguments.ticks}   "
        f"scored window: final {arguments.window}   "
        f"seeds: {arguments.seeds}   "
        f"learning shifts: {arguments.learning_shifts}"
    )
    print()

    structured_wins = 0
    structured_total = 0
    control_margin = 0.0
    worst_magnitude = 0
    score_low = 0
    score_high = 0
    layout_wins = {HISTORY_LAYOUT: 0, SITUATIONAL_LAYOUT: 0}

    for player_type in PLAYER_TYPES:
        summaries, magnitude, (low, high) = run_player(
            player_type,
            embeddings=embeddings,
            shifts=shifts,
            ticks=arguments.ticks,
            window=arguments.window,
            seeds=arguments.seeds,
            base_seed=arguments.base_seed,
        )
        worst_magnitude = max(worst_magnitude, magnitude)
        score_low = min(score_low, low)
        score_high = max(score_high, high)

        print(f"{player_type.name}")
        print(f"  {'method':<26}{'bytes':>8}{'window':>9}")
        for summary in summaries:
            size = f"{summary.storage_bytes}" if summary.storage_bytes else "-"
            print(
                f"  {summary.name:<26}{size:>8}{summary.window_accuracy * 100:>8.1f}%"
            )

        best_table = max(
            (item for item in summaries if item.kind == "table"),
            key=lambda item: item.window_accuracy,
        )
        best_model = max(
            (item for item in summaries if item.kind == "model"),
            key=lambda item: item.window_accuracy,
        )
        uniform = next(item for item in summaries if item.kind == "uniform")
        margin = best_model.window_accuracy - best_table.window_accuracy

        print(
            f"  -> best table {best_table.window_accuracy * 100:.1f}%   "
            f"best model {best_model.window_accuracy * 100:.1f}%   "
            f"margin {margin * 100:+.1f}pp   ({best_model.name})"
        )
        print()

        if player_type.name == "RANDOM":
            control_margin = best_model.window_accuracy - uniform.window_accuracy
        else:
            structured_total += 1
            if margin >= REQUIRED_MARGIN:
                structured_wins += 1
            for layout in layout_wins:
                if f"/{layout}/" in best_model.name:
                    layout_wins[layout] += 1

    largest = MimicConfig(layout=SITUATIONAL_LAYOUT, embedding=max(embeddings))
    parameters = MimicPredictor(largest).model.parameter_count

    print("Phase A gates")
    beat = f"{structured_wins}/{structured_total} structured players"
    print(
        f"  {'PASS' if structured_wins >= REQUIRED_WINS else 'FAIL'}  "
        f"model beats best table by >={REQUIRED_MARGIN * 100:.0f}pp on {beat}"
    )
    print(
        f"  {'PASS' if control_margin <= NOISE_MARGIN else 'FAIL'}  "
        f"negative control: model over uniform on RANDOM "
        f"{control_margin * 100:+.1f}pp (limit {NOISE_MARGIN * 100:.0f}pp)"
    )
    print(
        f"  {'PASS' if parameters <= PARAMETER_CEILING else 'FAIL'}  "
        f"largest candidate {parameters} parameters "
        f"(ceiling {PARAMETER_CEILING})"
    )
    print(
        f"  {'PASS' if worst_magnitude <= 127 else 'FAIL'}  "
        f"observed context magnitude {worst_magnitude} (signed byte limit 127)"
    )
    print(
        f"  {'PASS' if -32768 <= score_low and score_high <= 32767 else 'FAIL'}  "
        f"observed score range {score_low} to {score_high}"
    )
    print()
    print(
        f"  layout preference: history {layout_wins[HISTORY_LAYOUT]}, "
        f"situational {layout_wins[SITUATIONAL_LAYOUT]} "
        f"(of {structured_total} structured players)"
    )


if __name__ == "__main__":
    main()
