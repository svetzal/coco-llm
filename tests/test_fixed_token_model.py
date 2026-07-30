from pathlib import Path

import pytest
from fixed_token_lm import FixedTokenLanguageModel
from token_lm import ModelConfig, build_vocabulary, load_names, make_examples

CORPUS = (
    Path(__file__).parents[1]
    / "experiments"
    / "data"
    / "EXP-002-tokenized-computer-names.txt"
)


def test_fixed_model_is_deterministic_and_reduces_loss() -> None:
    names = load_names(CORPUS)
    vocabulary, token_by_text = build_vocabulary(names)
    contexts, targets = make_examples(names, token_by_text, context_size=2)
    first = FixedTokenLanguageModel(ModelConfig(), vocabulary)
    second = FixedTokenLanguageModel(ModelConfig(), vocabulary)

    initial_loss = first.loss(contexts, targets)
    first.train(contexts, targets, epochs=5)
    second.train(contexts, targets, epochs=5)

    assert first.loss(contexts, targets) < initial_loss
    assert first.checksum() == second.checksum()


def test_fixed_softmax_is_a_probability_distribution() -> None:
    names = load_names(CORPUS)
    vocabulary, token_by_text = build_vocabulary(names)
    contexts, _ = make_examples(names, token_by_text, context_size=2)
    model = FixedTokenLanguageModel(ModelConfig(), vocabulary)

    for context in contexts:
        _, probabilities = model._forward(context)

        assert int(probabilities.sum()) == 256
        assert int(probabilities.min()) >= 0
        assert int(probabilities.max()) <= 256


def test_generation_can_start_from_visible_prompt_tokens() -> None:
    names = load_names(CORPUS)
    vocabulary, token_by_text = build_vocabulary(names)
    contexts, targets = make_examples(names, token_by_text, context_size=2)
    model = FixedTokenLanguageModel(ModelConfig(), vocabulary)
    model.train(contexts, targets, epochs=20)

    completion = model.generate(
        prompt="COMMODORE",
        random_seed=6809,
        minimum_tokens=0,
        greedy=True,
    )

    assert completion


def test_generation_rejects_unknown_prompt_tokens() -> None:
    names = load_names(CORPUS)
    vocabulary, _ = build_vocabulary(names)
    model = FixedTokenLanguageModel(ModelConfig(), vocabulary)

    with pytest.raises(ValueError, match="unknown token"):
        model.generate(
            prompt="IBM",
            random_seed=6809,
            minimum_tokens=0,
            greedy=True,
        )
