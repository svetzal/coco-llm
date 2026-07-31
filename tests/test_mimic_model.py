import numpy as np
from duel_arena import (
    HISTORY_LAYOUT,
    MOVE_COUNT,
    PLAYER_BY_NAME,
    SITUATIONAL_LAYOUT,
    generate_stream,
)
from mimic_lm import (
    MarginalBaseline,
    MimicConfig,
    MimicModel,
    MimicPredictor,
    TableBaseline,
    UniformBaseline,
    evaluate_stream,
)


def test_parameter_counts_match_the_declared_formula() -> None:
    for layout, inputs in ((HISTORY_LAYOUT, 9), (SITUATIONAL_LAYOUT, 20)):
        for embedding in (4, 6, 8):
            model = MimicModel(MimicConfig(layout=layout, embedding=embedding))
            expected = inputs * embedding * 5 + MOVE_COUNT * embedding + MOVE_COUNT

            assert model.parameter_count == expected


def test_every_candidate_fits_the_declared_parameter_ceiling() -> None:
    for layout in (HISTORY_LAYOUT, SITUATIONAL_LAYOUT):
        for embedding in (4, 6, 8):
            model = MimicModel(MimicConfig(layout=layout, embedding=embedding))

            assert model.parameter_count <= 1024


def test_prediction_multiplies_stay_within_the_frame_budget() -> None:
    model = MimicModel(MimicConfig(layout=SITUATIONAL_LAYOUT, embedding=8))

    assert model.prediction_multiplies == 72
    assert model.training_multiplies == 216


def test_initialization_is_deterministic_for_a_seed() -> None:
    config = MimicConfig(layout=SITUATIONAL_LAYOUT, seed=6809)
    first = MimicModel(config)
    second = MimicModel(config)

    assert np.array_equal(first.position_embeddings, second.position_embeddings)
    assert np.array_equal(first.output_weights, second.output_weights)


def test_softmax_is_a_probability_distribution_in_units_of_256() -> None:
    model = MimicModel(MimicConfig(layout=SITUATIONAL_LAYOUT))
    stream = generate_stream(PLAYER_BY_NAME["HABIT"], ticks=40, seed=3)

    for record, _ in stream:
        context = record.context(SITUATIONAL_LAYOUT)
        vector = model._context_vector(context)
        probabilities = model._softmax(model._logits(vector))

        assert int(probabilities.sum()) == 256
        assert int(probabilities.min()) >= 0
        assert int(probabilities.max()) <= 256


def test_prediction_agrees_with_the_top_of_the_ranking() -> None:
    model = MimicModel(MimicConfig(layout=HISTORY_LAYOUT))
    stream = generate_stream(PLAYER_BY_NAME["ZIGZAG"], ticks=60, seed=7)

    for record, move in stream:
        context = record.context(HISTORY_LAYOUT)
        model.train_context(context, move)

        assert model.predict_context(context) == int(model.rank_context(context)[0])


def test_repeated_training_moves_prediction_toward_the_target() -> None:
    model = MimicModel(MimicConfig(layout=HISTORY_LAYOUT))
    context = (1, 2, 3, 4, 5)

    for _ in range(40):
        model.train_context(context, 6)

    assert model.predict_context(context) == 6


def test_context_and_score_stay_inside_their_declared_widths() -> None:
    model = MimicModel(MimicConfig(layout=SITUATIONAL_LAYOUT, embedding=8))
    stream = generate_stream(PLAYER_BY_NAME["PANIC"], ticks=600, seed=29)

    for record, move in stream:
        model.train_context(record.context(SITUATIONAL_LAYOUT), move)

    assert model.max_context_magnitude <= 127
    assert model.minimum_score >= -32768
    assert model.maximum_score <= 32767


def test_table_backoff_predicts_before_its_full_order_is_seen() -> None:
    table = TableBaseline(2)
    stream = generate_stream(PLAYER_BY_NAME["ZIGZAG"], ticks=4, seed=2)
    record, move = stream[0]
    table.observe(record, move)

    assert 0 <= table.predict(stream[1][0]) < MOVE_COUNT


def test_table_counter_cells_are_reported_for_the_memory_comparison() -> None:
    assert TableBaseline(1).counter_cells == 9 + 81
    assert TableBaseline(2).counter_cells == 9 + 81 + 729


def test_no_method_beats_uniform_on_a_uniform_player() -> None:
    stream = generate_stream(PLAYER_BY_NAME["RANDOM"], ticks=600, seed=41)
    predictors = [
        UniformBaseline(seed=41),
        TableBaseline(2),
        MimicPredictor(MimicConfig(layout=SITUATIONAL_LAYOUT, seed=41)),
    ]
    results = evaluate_stream(stream, predictors, window=200)

    for result in results:
        assert result.window_accuracy < 0.25


def test_the_model_learns_a_bearing_driven_player() -> None:
    stream = generate_stream(PLAYER_BY_NAME["FLEE"], ticks=600, seed=43)
    predictors = [
        MarginalBaseline(),
        MimicPredictor(MimicConfig(layout=SITUATIONAL_LAYOUT, seed=43)),
    ]
    marginal, model = evaluate_stream(stream, predictors, window=200)

    assert model.window_accuracy > marginal.window_accuracy


def test_evaluation_scores_the_requested_trailing_window() -> None:
    stream = generate_stream(PLAYER_BY_NAME["HABIT"], ticks=300, seed=47)
    results = evaluate_stream(stream, [MarginalBaseline()], window=100)

    assert results[0].ticks == 300
    assert 0.0 <= results[0].window_accuracy <= 1.0
    assert 0.0 <= results[0].overall_accuracy <= 1.0
