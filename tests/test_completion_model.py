from pathlib import Path

import numpy as np
import pytest
from completion_lm import (
    AdditiveCompletionModel,
    BackoffNGramPredictor,
    HiddenCompletionModel,
    Int8AdditiveModel,
    NeuralConfig,
    build_completion_vocabulary,
    build_sequence_vocabulary,
    evaluate,
    largest_additive_embedding,
    largest_hidden_width,
    load_phrases,
    load_token_sequences,
    make_completion_examples,
    make_sequence_examples,
    quantize_q4_4,
    suggest,
    tokenize_sentence,
    train_neural_model,
)

ROOT = Path(__file__).parents[1]
TRAINING = ROOT / "experiments" / "data" / "EXP-006-completion-training.txt"
HOLDOUT = ROOT / "experiments" / "data" / "EXP-006-completion-holdout.txt"
EXP7_TRAINING = ROOT / "experiments" / "data" / "EXP-007-sentence-training.txt"
EXP7_HOLDOUT = ROOT / "experiments" / "data" / "EXP-007-sentence-holdout.txt"


def completion_data():
    training = load_phrases(TRAINING)
    holdout = load_phrases(HOLDOUT)
    vocabulary, token_by_text = build_completion_vocabulary(training)
    training_examples = make_completion_examples(training, token_by_text, 4)
    holdout_examples = make_completion_examples(holdout, token_by_text, 4)
    return vocabulary, training_examples, holdout_examples


def test_holdout_uses_training_vocabulary() -> None:
    training = load_phrases(TRAINING)
    holdout = load_phrases(HOLDOUT)
    _, token_by_text = build_completion_vocabulary(training)

    assert {
        word
        for phrase in holdout
        for word in phrase.split()
        if word not in token_by_text
    } == set()


def test_exp7_corpus_respects_model_and_holdout_boundaries() -> None:
    training = load_token_sequences(EXP7_TRAINING)
    holdout = load_token_sequences(EXP7_HOLDOUT)
    vocabulary, token_by_text = build_sequence_vocabulary(training)
    training_sequences = {tuple(sequence) for sequence in training}
    holdout_sequences = {tuple(sequence) for sequence in holdout}

    assert len(training) == 423
    assert len(holdout) == 61
    assert len(vocabulary) == 255
    assert len(training_sequences) == len(training)
    assert len(holdout_sequences) == len(holdout)
    assert training_sequences.isdisjoint(holdout_sequences)
    assert {
        token
        for sequence in holdout
        for token in sequence
        if token not in token_by_text
    } == set()


def test_sentence_tokenization_preserves_punctuation_as_tokens(tmp_path) -> None:
    path = tmp_path / "sentences.txt"
    path.write_text(
        "The CoCo predicts, humans decide.\nIs this useful? Yes!\n",
        encoding="ascii",
    )

    sequences = load_token_sequences(path)
    vocabulary, token_by_text = build_sequence_vocabulary(sequences)
    contexts, targets = make_sequence_examples(sequences, token_by_text, 5)

    assert tokenize_sentence("The CoCo predicts, humans decide.") == [
        "THE",
        "COCO",
        "PREDICTS",
        ",",
        "HUMANS",
        "DECIDE",
        ".",
    ]
    assert all(mark in vocabulary for mark in (".", ",", "?", "!"))
    assert contexts.shape == (15, 5)
    assert targets.shape == (15,)


def test_sentence_tokenization_rejects_unsupported_characters() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        tokenize_sentence('THE COCO SAYS "HELLO"')


def test_budget_dimensions_fit_one_byte_weight_budget() -> None:
    vocabulary, _, _ = completion_data()
    additive_embedding = largest_additive_embedding(len(vocabulary), 4, 8192)
    hidden_width = largest_hidden_width(len(vocabulary), 4, 8, 8192)
    additive = AdditiveCompletionModel(
        NeuralConfig(context=4, embedding=additive_embedding), vocabulary
    )
    hidden = HiddenCompletionModel(
        NeuralConfig(context=4, embedding=8, hidden=hidden_width), vocabulary
    )

    assert additive.parameter_count <= 8192
    assert hidden.parameter_count <= 8192
    assert (
        AdditiveCompletionModel(
            NeuralConfig(context=4, embedding=additive_embedding + 1),
            vocabulary,
        ).parameter_count
        > 8192
    )
    assert (
        HiddenCompletionModel(
            NeuralConfig(context=4, embedding=8, hidden=hidden_width + 1),
            vocabulary,
        ).parameter_count
        > 8192
    )


def test_q4_4_quantization_is_signed_and_saturating() -> None:
    values = np.asarray([-9.0, -0.03, 0.04, 8.5])

    assert quantize_q4_4(values).tolist() == [-8.0, 0.0, 0.0625, 7.9375]


def test_int8_additive_scores_match_quantized_float_ranking() -> None:
    vocabulary, training_examples, holdout_examples = completion_data()
    training_contexts, training_targets = training_examples
    holdout_contexts, _ = holdout_examples
    model = AdditiveCompletionModel(NeuralConfig(context=4, embedding=3), vocabulary)
    train_neural_model(
        model,
        training_contexts,
        training_targets,
        epochs=2,
        learning_rate=0.01,
        batch_size=64,
    )
    quantized = model.quantized_copy()
    fixed = model.int8_copy()

    assert isinstance(fixed, Int8AdditiveModel)
    for context in holdout_contexts[:20]:
        assert np.array_equal(
            np.argsort(-quantized.scores(context), kind="stable"),
            np.argsort(-fixed.scores(context), kind="stable"),
        )
    assert len(fixed.model_bytes(padded_size=8192)) == 8192


def test_int8_additive_supports_signed_q2_2_parameters() -> None:
    model = AdditiveCompletionModel(
        NeuralConfig(context=1, embedding=1), ["<END>", "COCO"]
    )
    model.position_embeddings[:] = [[[-3.0], [3.0]]]
    model.output_weights[:] = [[-2.5], [2.5]]
    model.output_biases[:] = [-3.0, 3.0]

    fixed = model.int8_copy(fractional_bits=2, value_bits=4)

    assert fixed.position_embeddings.flatten().tolist() == [-8, 7]
    assert fixed.output_weights.flatten().tolist() == [-8, 7]
    assert fixed.output_biases.tolist() == [-8, 7]
    assert fixed.integer_scores(np.asarray([1])).tolist() == [-88, 77]


def test_ngram_evaluation_and_prefix_suggestions() -> None:
    vocabulary, training_examples, holdout_examples = completion_data()
    training_contexts, training_targets = training_examples
    holdout_contexts, holdout_targets = holdout_examples
    model = BackoffNGramPredictor(vocabulary, training_contexts, training_targets)

    metrics = evaluate(model, holdout_contexts, holdout_targets)

    assert metrics.lexical_examples > 0
    assert 0.0 <= metrics.top_three_accuracy <= 1.0
    assert 0.0 <= metrics.keystroke_savings <= 1.0
    assert suggest(model, ["PRESS", "TAB", "TO"], prefix="C")[0] in {
        "COMPLETE",
        "CONTINUE",
    }


def test_hidden_training_is_deterministic_and_reduces_loss() -> None:
    vocabulary, training_examples, _ = completion_data()
    contexts, targets = training_examples
    config = NeuralConfig(context=4, embedding=4, hidden=6)
    first = HiddenCompletionModel(config, vocabulary)
    second = HiddenCompletionModel(config, vocabulary)

    first_losses = train_neural_model(
        first,
        contexts,
        targets,
        epochs=2,
        learning_rate=0.01,
        batch_size=64,
    )
    train_neural_model(
        second,
        contexts,
        targets,
        epochs=2,
        learning_rate=0.01,
        batch_size=64,
    )

    assert first_losses[-1] < first_losses[0]
    for first_parameter, second_parameter in zip(
        first.parameters, second.parameters, strict=True
    ):
        assert np.array_equal(first_parameter, second_parameter)
