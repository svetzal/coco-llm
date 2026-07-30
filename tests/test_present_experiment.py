import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

from present_experiment import (
    EXPERIMENTS,
    build_exp_005_reference,
    fan_counts,
    normalize_experiment,
)


def test_experiment_aliases_are_easy_to_type() -> None:
    assert normalize_experiment("4") == "EXP-004"
    assert normalize_experiment("EXP-004") == "EXP-004"
    assert normalize_experiment("005") == "EXP-005"


def test_presentation_experiments_start_with_complete_6809_training() -> None:
    assert list(EXPERIMENTS) == ["EXP-004", "EXP-005"]


def test_marketing_language_demo_has_memorable_prompt_completions() -> None:
    payload = build_exp_005_reference()

    assert payload["parameters"] == 380
    assert payload["vocabulary"] == 38
    assert payload["completions"] == [
        {"prompt": "I ADORE", "completion": "MY 64"},
        {
            "prompt": "ARE YOU",
            "completion": "KEEPING UP IN LITTLE COMPUTERS",
        },
        {"prompt": "WHY BUY", "completion": "JUST A VIDEO GAME"},
        {"prompt": "POWER WITHOUT", "completion": "THE PRICE"},
        {
            "prompt": "GET YOUR",
            "completion": "START IN COLOR COMPUTING",
        },
        {
            "prompt": "THE COMPUTER",
            "completion": "FOR THE REST OF US",
        },
    ]


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
