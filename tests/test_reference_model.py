from pathlib import Path

import numpy as np
from coco_lm import (
    VOCABULARY,
    CharacterLanguageModel,
    ModelConfig,
    load_names,
    make_examples,
)

CORPUS = (
    Path(__file__).parents[1] / "experiments" / "data" / "EXP-001-computer-names.txt"
)


def test_candidate_model_has_expected_size() -> None:
    model = CharacterLanguageModel(ModelConfig())

    assert len(VOCABULARY) == 40
    assert model.parameter_count == 460
    assert model.multiplies_per_example == 882


def test_corpus_is_supported_and_examples_are_bounded() -> None:
    names = load_names(CORPUS)
    contexts, targets = make_examples(names, context_size=3)

    assert len(names) == 48
    assert contexts.shape == (sum(len(name) + 1 for name in names), 3)
    assert np.all(contexts >= 0)
    assert np.all(contexts < len(VOCABULARY))
    assert np.all(targets >= 0)
    assert np.all(targets < len(VOCABULARY))


def test_training_is_deterministic_and_reduces_loss() -> None:
    names = load_names(CORPUS)[:8]
    contexts, targets = make_examples(names, context_size=3)
    first = CharacterLanguageModel(ModelConfig())
    second = CharacterLanguageModel(ModelConfig())

    initial_loss = first.loss(contexts, targets)
    first.train(contexts, targets, epochs=2, learning_rate=0.05)
    second.train(contexts, targets, epochs=2, learning_rate=0.05)

    assert first.loss(contexts, targets) < initial_loss
    assert first.checksum() == second.checksum()
