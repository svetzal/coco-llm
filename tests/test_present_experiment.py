import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

from present_experiment import EXPERIMENTS, fan_counts, normalize_experiment


def test_experiment_aliases_are_easy_to_type() -> None:
    assert normalize_experiment("1") == "EXP-001"
    assert normalize_experiment("002") == "EXP-002"
    assert normalize_experiment("exp-3") == "EXP-003"
    assert normalize_experiment("EXP-004") == "EXP-004"


def test_all_recorded_experiments_are_presentable() -> None:
    assert list(EXPERIMENTS) == ["EXP-001", "EXP-002", "EXP-003", "EXP-004"]


def test_fan_counts_group_non_brand_outputs_as_other() -> None:
    result = SimpleNamespace(
        first_token_counts={
            "APPLE": 10,
            "COMMODORE": 4,
            "TANDY": 3,
            "ACORN": 2,
            "64": 1,
        }
    )

    assert fan_counts(result) == (10, 4, 3, 3)
