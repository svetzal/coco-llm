from duel_arena import (
    ARENA_HEIGHT,
    ARENA_WIDTH,
    BEARING_BASE,
    CONTEXT_SIZE,
    HISTORY_LAYOUT,
    IDLE,
    MOVE_COUNT,
    MOVE_DELTAS,
    PLAYER_TYPES,
    RANGE_BASE,
    SITUATIONAL_LAYOUT,
    SITUATIONAL_VOCABULARY,
    Arena,
    direction_index,
    generate_stream,
    input_vocabulary_size,
    range_bucket,
    rotate_move,
)


def test_direction_index_is_zero_only_for_a_zero_vector() -> None:
    assert direction_index(0, 0) == IDLE

    for delta_x in range(-8, 9):
        for delta_y in range(-8, 9):
            if delta_x == 0 and delta_y == 0:
                continue
            assert direction_index(delta_x, delta_y) != IDLE


def test_direction_index_points_the_same_way_as_its_vector() -> None:
    for delta_x in range(-8, 9):
        for delta_y in range(-8, 9):
            if delta_x == 0 and delta_y == 0:
                continue
            step_x, step_y = MOVE_DELTAS[direction_index(delta_x, delta_y)]

            assert step_x * delta_x >= 0
            assert step_y * delta_y >= 0


def test_rotating_four_eighths_reverses_a_move() -> None:
    for move in range(1, MOVE_COUNT):
        step_x, step_y = MOVE_DELTAS[move]
        opposite_x, opposite_y = MOVE_DELTAS[rotate_move(move, 4)]

        assert (opposite_x, opposite_y) == (-step_x, -step_y)


def test_rotating_a_full_turn_is_identity() -> None:
    for move in range(MOVE_COUNT):
        assert rotate_move(move, 8) == move


def test_range_buckets_increase_with_distance() -> None:
    assert range_bucket(0, 0) == 0
    assert range_bucket(6, 0) == 0
    assert range_bucket(7, 0) == 1
    assert range_bucket(16, 3) == 1
    assert range_bucket(17, 0) == 2


def test_player_stays_inside_the_arena() -> None:
    arena = Arena(player=(0, 0), opponent=(40, 20))

    for _ in range(40):
        arena.apply(8)

    assert 0 <= arena.player_x < ARENA_WIDTH
    assert 0 <= arena.player_y < ARENA_HEIGHT


def test_history_records_intent_even_when_the_wall_blocks_it() -> None:
    arena = Arena(player=(0, 0), opponent=(40, 20))
    arena.apply(7)

    assert arena.player_x == 0
    assert arena.history[-1] == 7


def test_opponent_closes_but_never_overlaps() -> None:
    arena = Arena(player=(10, 10), opponent=(40, 10))

    for _ in range(400):
        arena.apply(IDLE)

    assert arena.delta != (0, 0)


def test_context_shape_and_range_match_the_layout() -> None:
    stream = generate_stream(PLAYER_TYPES[0], ticks=50, seed=17)

    for record, _ in stream:
        history = record.context(HISTORY_LAYOUT)
        situational = record.context(SITUATIONAL_LAYOUT)

        assert len(history) == CONTEXT_SIZE
        assert len(situational) == CONTEXT_SIZE
        assert all(0 <= token < MOVE_COUNT for token in history)
        assert BEARING_BASE <= situational[0] < RANGE_BASE
        assert RANGE_BASE <= situational[1] < SITUATIONAL_VOCABULARY
        assert all(0 <= token < MOVE_COUNT for token in situational[2:])


def test_input_vocabulary_sizes_bound_every_generated_token() -> None:
    stream = generate_stream(PLAYER_TYPES[5], ticks=200, seed=23)

    for layout in (HISTORY_LAYOUT, SITUATIONAL_LAYOUT):
        limit = input_vocabulary_size(layout)

        for record, _ in stream:
            assert all(0 <= token < limit for token in record.context(layout))


def test_streams_are_deterministic_and_seed_dependent() -> None:
    for player_type in PLAYER_TYPES:
        first = [move for _, move in generate_stream(player_type, ticks=80, seed=5)]
        again = [move for _, move in generate_stream(player_type, ticks=80, seed=5)]
        other = [move for _, move in generate_stream(player_type, ticks=80, seed=6)]

        assert first == again
        assert first != other


def test_every_player_emits_only_legal_moves() -> None:
    for player_type in PLAYER_TYPES:
        stream = generate_stream(player_type, ticks=120, seed=11)

        assert all(0 <= move < MOVE_COUNT for (move,) in ((m,) for _, m in stream))


def test_flee_moves_away_from_the_opponent_most_of_the_time() -> None:
    flee = next(item for item in PLAYER_TYPES if item.name == "FLEE")
    stream = generate_stream(flee, ticks=300, seed=13)
    agreed = sum(
        1 for record, move in stream if move == rotate_move(record.bearing + 1, 4)
    )

    assert agreed / len(stream) > 0.8
