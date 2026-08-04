import numpy as np
from associative_attention import (
    AssociativeAttention,
    generate_recall_batch,
    tail_oracle_predictions,
)


def test_generated_target_is_bound_to_query() -> None:
    batch = generate_recall_batch(np.random.default_rng(1), examples=32)
    rows = np.arange(len(batch))

    assert np.array_equal(batch.queries, batch.memory_keys[rows, batch.target_slots])
    assert np.array_equal(batch.targets, batch.memory_values[rows, batch.target_slots])


def test_attention_learns_novel_bindings_and_survives_quantization() -> None:
    training = generate_recall_batch(np.random.default_rng(2), examples=1024)
    test = generate_recall_batch(np.random.default_rng(3), examples=1024)
    model = AssociativeAttention(key_count=16, width=5)

    model.train(training, epochs=400)

    assert model.accuracy(test) > 0.99
    assert model.quantized_copy().accuracy(test) > 0.99


def test_tail_oracle_only_recalls_visible_records() -> None:
    training = generate_recall_batch(np.random.default_rng(4), examples=1024)
    test = generate_recall_batch(np.random.default_rng(5), examples=4096)

    one = tail_oracle_predictions(training, test, value_count=8, visible_records=1)
    four = tail_oracle_predictions(training, test, value_count=8, visible_records=4)

    assert np.mean(one == test.targets) < 0.30
    assert 0.50 < np.mean(four == test.targets) < 0.65
