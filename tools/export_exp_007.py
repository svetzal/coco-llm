#!/usr/bin/env python3
"""Train and export the EXP-007 inference-only CoCo model image."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from completion_lm import (
    AdditiveCompletionModel,
    NeuralConfig,
    build_sequence_vocabulary,
    evaluate,
    largest_additive_embedding,
    load_token_sequences,
    make_sequence_examples,
    train_neural_model,
)

DEFAULT_TRAINING = ROOT / "experiments" / "data" / "EXP-007-sentence-training.txt"
DEFAULT_HOLDOUT = ROOT / "experiments" / "data" / "EXP-007-sentence-holdout.txt"
MODEL_BYTES = 32768
CONTEXT_SIZE = 5


def assembly_bytes(values: bytes, *, width: int = 16) -> list[str]:
    return [
        "        fcb     "
        + ",".join(f"${value:02x}" for value in values[offset : offset + width])
        for offset in range(0, len(values), width)
    ]


def token_label(token: str, index: int) -> str:
    safe = "".join(character if character.isalnum() else "_" for character in token)
    return f"exp7_token_{index:03d}_{safe}"


def decb_binary(payload: bytes, *, load_address: int) -> bytes:
    if not 0 <= load_address <= 0xFFFF:
        raise ValueError("load address must be a 16-bit value")
    if len(payload) > 0xFFFF:
        raise ValueError("DECB block cannot exceed 65,535 bytes")
    return b"".join(
        (
            b"\x00",
            len(payload).to_bytes(2, "big"),
            load_address.to_bytes(2, "big"),
            payload,
            b"\xff\x00\x00\x00\x00",
        )
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training", type=Path, default=DEFAULT_TRAINING)
    parser.add_argument("--holdout", type=Path, default=DEFAULT_HOLDOUT)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=ROOT / "build" / "exp007",
    )
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument(
        "--load-address", type=lambda text: int(text, 0), default=0x7F00
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    sequences = load_token_sequences(arguments.training)
    holdout_sequences = load_token_sequences(arguments.holdout)
    vocabulary, token_by_text = build_sequence_vocabulary(sequences)
    if len(vocabulary) > 255:
        raise ValueError(f"{len(vocabulary)} tokens exceed the byte-token limit")
    unknown = sorted(
        {
            token
            for sequence in holdout_sequences
            for token in sequence
            if token not in token_by_text
        }
    )
    if unknown:
        raise ValueError(f"holdout contains unknown tokens: {', '.join(unknown)}")
    contexts, targets = make_sequence_examples(sequences, token_by_text, CONTEXT_SIZE)
    holdout_contexts, holdout_targets = make_sequence_examples(
        holdout_sequences, token_by_text, CONTEXT_SIZE
    )
    embedding = largest_additive_embedding(len(vocabulary), CONTEXT_SIZE, MODEL_BYTES)
    model = AdditiveCompletionModel(
        NeuralConfig(context=CONTEXT_SIZE, embedding=embedding),
        vocabulary,
    )
    losses = train_neural_model(
        model,
        contexts,
        targets,
        epochs=arguments.epochs,
        learning_rate=0.01,
        batch_size=32,
    )
    fixed = model.int8_copy()
    image = fixed.model_bytes(padded_size=MODEL_BYTES)
    context_vectors = [fixed.context_vector(context) for context in contexts]
    maximum_context_magnitude = max(
        abs(int(value)) for vector in context_vectors for value in vector
    )
    if maximum_context_magnitude > 127:
        raise ValueError("observed context vector does not fit signed 8-bit")
    all_context_minimum = np.min(
        fixed.position_embeddings.astype(np.int64), axis=1
    ).sum(axis=0)
    all_context_maximum = np.max(
        fixed.position_embeddings.astype(np.int64), axis=1
    ).sum(axis=0)
    all_context_magnitude = int(
        max(
            np.max(np.abs(all_context_minimum)),
            np.max(np.abs(all_context_maximum)),
        )
    )
    if all_context_magnitude > 127:
        raise ValueError("some possible context vector does not fit signed 8-bit")
    minimum_scores: list[int] = []
    maximum_scores: list[int] = []
    for weights, bias in zip(
        fixed.output_weights.astype(np.int64),
        fixed.output_biases.astype(np.int64),
        strict=True,
    ):
        minimum_score = int(bias) * 16
        maximum_score = int(bias) * 16
        for weight, minimum, maximum in zip(
            weights,
            all_context_minimum,
            all_context_maximum,
            strict=True,
        ):
            low = int(weight) * int(minimum)
            high = int(weight) * int(maximum)
            minimum_score += min(low, high)
            maximum_score += max(low, high)
        minimum_scores.append(minimum_score)
        maximum_scores.append(maximum_score)
    possible_score_minimum = min(minimum_scores)
    possible_score_maximum = max(maximum_scores)
    if possible_score_minimum < -32768 or possible_score_maximum > 32767:
        raise ValueError(
            "some possible output score does not fit signed 16-bit: "
            f"{possible_score_minimum}..{possible_score_maximum}"
        )

    output = arguments.output_directory
    output.mkdir(parents=True, exist_ok=True)
    (output / "weights.bin").write_bytes(image)
    (output / "weights.decb").write_bytes(
        decb_binary(image, load_address=arguments.load_address)
    )
    (output / "vocabulary.txt").write_text(
        "\n".join(vocabulary) + "\n", encoding="ascii"
    )

    prompts = [
        ["PRESS", "TAB", "TO"],
        ["THE", "COMMODORE", "64", "IS"],
        ["THE", "MODEL", "CAN"],
        ["IS", "PREDICTION"],
        ["BETTER", "DATA", "MAKES"],
    ]
    tests = []
    boundary = token_by_text["<END>"]
    for words in prompts:
        context = [boundary] * CONTEXT_SIZE
        for word in words[-CONTEXT_SIZE:]:
            context = context[1:] + [token_by_text[word]]
        integer_scores = fixed.integer_scores(context_array(context))
        ranking = sorted(
            range(len(vocabulary)),
            key=lambda index: (-int(integer_scores[index]), index),
        )
        ranking = [index for index in ranking if index != boundary][:3]
        tests.append(
            {
                "prompt": " ".join(words),
                "context_tokens": context,
                "context_vector": [
                    int(value) for value in fixed.context_vector(context_array(context))
                ],
                "top_three_tokens": ranking,
                "top_three_words": [vocabulary[index] for index in ranking],
                "top_three_scores": [int(integer_scores[index]) for index in ranking],
            }
        )
    (output / "test-vectors.json").write_text(
        json.dumps(tests, indent=2) + "\n", encoding="ascii"
    )
    first_test = tests[0]
    assembly = [
        "; Generated by tools/export_exp_007.py. Do not edit.",
        f"EXP7_VOCAB_SIZE        equ     {len(vocabulary)}",
        f"EXP7_CONTEXT_SIZE      equ     {CONTEXT_SIZE}",
        f"EXP7_EMBED_DIMS        equ     {embedding}",
        (f"EXP7_POSITION_STRIDE   equ     {len(vocabulary) * embedding}"),
        f"EXP7_PARAM_COUNT       equ     {fixed.parameter_count}",
        f"EXP7_MODEL_BASE        equ     ${arguments.load_address:04x}",
        (
            "EXP7_OUTPUT_WEIGHTS    equ     "
            f"EXP7_MODEL_BASE+{fixed.position_embeddings.size}"
        ),
        (
            "EXP7_OUTPUT_BIASES     equ     "
            f"EXP7_OUTPUT_WEIGHTS+{fixed.output_weights.size}"
        ),
        f"EXP7_TOKEN_PERIOD       equ     {token_by_text['.']}",
        f"EXP7_TOKEN_COMMA        equ     {token_by_text[',']}",
        f"EXP7_TOKEN_QUESTION     equ     {token_by_text['?']}",
        f"EXP7_TOKEN_EXCLAMATION  equ     {token_by_text['!']}",
        f"EXP7_TOKEN_COLON        equ     {token_by_text[':']}",
        f"EXP7_TOKEN_SEMICOLON    equ     {token_by_text[';']}",
        "",
        "exp7_test_context",
        "        fcb     "
        + ",".join(f"${token:02x}" for token in first_test["context_tokens"]),
        "exp7_expected_top_three",
        "        fcb     "
        + ",".join(f"${token:02x}" for token in first_test["top_three_tokens"]),
        "",
        "exp7_token_pointers",
    ]
    assembly.extend(
        f"        fdb     {token_label(token, index)}"
        for index, token in enumerate(vocabulary)
    )
    assembly.append("")
    for index, token in enumerate(vocabulary):
        assembly.append(token_label(token, index))
        assembly.extend(assembly_bytes(token.encode("ascii") + b"\x00"))
    (output / "model_data.inc").write_text("\n".join(assembly), encoding="ascii")
    model_image = [
        "; Generated by tools/export_exp_007.py. Do not edit.",
        "        org     EXP7_MODEL_BASE",
        "exp7_model_image",
        *assembly_bytes(image),
        "",
    ]
    (output / "model_image.inc").write_text("\n".join(model_image), encoding="ascii")

    offsets = {
        "position_embeddings": 0,
        "output_weights": fixed.position_embeddings.size,
        "output_biases": (fixed.position_embeddings.size + fixed.output_weights.size),
        "padding": fixed.parameter_count,
    }
    manifest = {
        "experiment": 7,
        "format": "signed Q4.4 bytes",
        "layout": offsets,
        "load_address": arguments.load_address,
        "context": CONTEXT_SIZE,
        "embedding": embedding,
        "vocabulary_size": len(vocabulary),
        "parameters": fixed.parameter_count,
        "image_bytes": len(image),
        "padding_bytes": len(image) - fixed.parameter_count,
        "inference_multiplies": fixed.inference_multiplies,
        "observed_maximum_context_magnitude": maximum_context_magnitude,
        "all_possible_maximum_context_magnitude": all_context_magnitude,
        "all_possible_score_range": [
            possible_score_minimum,
            possible_score_maximum,
        ],
        "epochs": arguments.epochs,
        "initial_epoch_loss": losses[0],
        "final_epoch_loss": losses[-1],
        "sha256": hashlib.sha256(image).hexdigest(),
        "holdout_metrics": asdict(evaluate(fixed, holdout_contexts, holdout_targets)),
        "sample_suggestions": {
            test["prompt"]: test["top_three_words"] for test in tests
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    print(f"wrote {len(image)} bytes to {output / 'weights.bin'}")
    print(f"SHA-256: {manifest['sha256']}")
    print(
        f"{len(vocabulary)} tokens, {fixed.parameter_count} parameters, "
        f"{fixed.inference_multiplies} multiplies/suggestion"
    )


def context_array(values: list[int]):
    return np.asarray(values, dtype=np.int64)


if __name__ == "__main__":
    main()
