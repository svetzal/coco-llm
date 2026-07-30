from pathlib import Path

from token_lm import (
    ModelConfig,
    TokenLanguageModel,
    build_vocabulary,
    load_names,
    make_examples,
)

CORPUS = (
    Path(__file__).parents[1]
    / "experiments"
    / "data"
    / "EXP-002-tokenized-computer-names.txt"
)


def test_live_model_has_expected_size() -> None:
    names = load_names(CORPUS)
    vocabulary, _ = build_vocabulary(names)
    model = TokenLanguageModel(ModelConfig(), vocabulary)

    assert len(vocabulary) == 29
    assert model.parameter_count == 290
    assert model.multiplies_per_example == 261


def test_live_corpus_has_expected_training_shape() -> None:
    names = load_names(CORPUS)
    _, token_by_text = build_vocabulary(names)
    contexts, targets = make_examples(names, token_by_text, context_size=2)

    assert len(names) == 18
    assert contexts.shape == (58, 2)
    assert targets.shape == (58,)


def test_live_training_is_deterministic_and_reduces_loss() -> None:
    names = load_names(CORPUS)
    vocabulary, token_by_text = build_vocabulary(names)
    contexts, targets = make_examples(names, token_by_text, context_size=2)
    first = TokenLanguageModel(ModelConfig(), vocabulary)
    second = TokenLanguageModel(ModelConfig(), vocabulary)

    initial_loss = first.loss(contexts, targets)
    first.train(contexts, targets, epochs=5, learning_rate=0.0625)
    second.train(contexts, targets, epochs=5, learning_rate=0.0625)

    assert first.loss(contexts, targets) < initial_loss
    assert first.checksum() == second.checksum()
