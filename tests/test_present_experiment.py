import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

import present_experiment
from present_experiment import (
    EXPERIMENTS,
    build_exp_005_reference,
    fan_counts,
    normalize_experiment,
)
from run_bias_demo import BiasResult


def test_experiment_aliases_are_easy_to_type() -> None:
    assert normalize_experiment("4") == "EXP-004"
    assert normalize_experiment("EXP-004") == "EXP-004"
    assert normalize_experiment("005") == "EXP-005"
    assert normalize_experiment("7") == "EXP-007"
    assert normalize_experiment("11") == "EXP-011"


def test_presentation_menu_follows_the_6809_learning_journey() -> None:
    assert list(EXPERIMENTS) == [
        "EXP-004",
        "EXP-005",
        "EXP-006",
        "EXP-007",
        "EXP-011",
    ]


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


def test_bias_presentation_names_changed_and_held_factors(monkeypatch, capsys) -> None:
    result = BiasResult(
        label="APPLE FAN",
        training_names=18,
        examples_per_epoch=54,
        epochs=30,
        training_updates=1620,
        initial_loss=1.0,
        final_loss=0.5,
        checksum="fixture",
        first_token_counts={"APPLE": 20},
        samples=["APPLE MACINTOSH"],
    )
    monkeypatch.setattr(
        present_experiment,
        "run_comparison",
        lambda sample_count: [result],
    )

    present_experiment.run_exp_003()

    output = capsys.readouterr().out
    assert "WHAT CHANGED: TRAINING DATA" in output
    assert "APPLE BLOCK -> COMMODORE BLOCK -> TANDY BLOCK" in output
    assert "WHAT DID NOT CHANGE" in output
    assert "Architecture, initialization seed, 1,620 updates" in output
