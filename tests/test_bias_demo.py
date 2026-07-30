from run_bias_demo import configured_runs, project_root, run_comparison, training_data
from token_lm import build_vocabulary, load_names


def test_bias_corpora_have_equal_training_budgets() -> None:
    root = project_root()
    vocabulary_names = load_names(
        root / "experiments" / "data" / "EXP-002-tokenized-computer-names.txt"
    )
    vocabulary_names += load_names(
        root / "experiments" / "data" / "EXP-003-all-fans.txt"
    )
    _, token_by_text = build_vocabulary(vocabulary_names)
    update_counts = []

    for run in configured_runs(root):
        _, _, targets = training_data(run, token_by_text, context_size=2)
        update_counts.append(len(targets) * run.epochs)

    assert update_counts == [1620, 1620, 1620, 1620, 1620]


def test_fan_models_reveal_their_training_bias() -> None:
    results = {result.label: result for result in run_comparison(sample_count=20)}

    assert results["APPLE FAN"].first_token_counts["APPLE"] >= 15
    assert results["COMMODORE FAN"].first_token_counts["COMMODORE"] >= 15
    assert results["TANDY FAN"].first_token_counts["TANDY"] >= 12


def test_combining_sets_does_not_erase_ordering_bias() -> None:
    results = {result.label: result for result in run_comparison(sample_count=20)}
    concatenated = results["ALL FANS CONCATENATED"].first_token_counts
    interleaved = results["ALL FANS INTERLEAVED"].first_token_counts

    assert concatenated["TANDY"] >= 12
    assert {"APPLE", "COMMODORE", "TANDY"} <= interleaved.keys()
    assert max(interleaved.values()) <= 12
