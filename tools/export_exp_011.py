#!/usr/bin/env python3
"""Train and export EXP-011's selected fixed-point attention head."""

from __future__ import annotations

import binascii
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from associative_attention import AssociativeAttention, generate_recall_batch

OUTPUT = ROOT / "build" / "exp011"
TRAINING_SEED = 1101
TEST_VECTOR_SEED = 1103
MODEL_SEED = 6809
TRAINING_EXAMPLES = 4096
EPOCHS = 400
KEY_COUNT = 16
VALUE_COUNT = 8
MEMORY_SIZE = 8
WIDTH = 5
FRACTIONAL_BITS = 4

DEMO_CONTEXTS = (
    ((0, 1, 2, 3, 4, 5, 6, 7), (7, 2, 5, 1, 4, 0, 6, 3)),
    ((3, 0, 6, 1, 5, 7, 2, 4), (5, 1, 3, 6, 7, 4, 0, 2)),
    ((5, 2, 7, 4, 1, 6, 0, 3), (3, 6, 1, 0, 4, 7, 2, 5)),
    ((1, 7, 4, 2, 6, 3, 5, 0), (0, 5, 7, 3, 1, 6, 2, 4)),
)


def quantize(values: np.ndarray) -> np.ndarray:
    scale = 1 << FRACTIONAL_BITS
    return np.clip(np.rint(values * scale), -128, 127).astype(np.int8)


def fcb_lines(label: str, values: np.ndarray) -> list[str]:
    flattened = values.reshape(-1).view(np.uint8)
    lines = [label]
    for start in range(0, len(flattened), 16):
        chunk = flattened[start : start + 16]
        lines.append(
            "        fcb     " + ",".join(f"${int(value):02x}" for value in chunk)
        )
    return lines


def main() -> None:
    training = generate_recall_batch(
        np.random.default_rng(TRAINING_SEED), TRAINING_EXAMPLES
    )
    model = AssociativeAttention(KEY_COUNT, WIDTH, seed=MODEL_SEED)
    model.train(training, epochs=EPOCHS)
    query_weights = quantize(model.query_embeddings)
    key_weights = quantize(model.key_embeddings)
    weights = query_weights.tobytes() + key_weights.tobytes()
    model_id = binascii.crc_hqx(weights, 0xFFFF)

    contexts = np.asarray(
        [
            [item for pair in zip(keys, values, strict=True) for item in pair]
            for keys, values in DEMO_CONTEXTS
        ],
        dtype=np.uint8,
    )
    vectors = generate_recall_batch(
        np.random.default_rng(TEST_VECTOR_SEED), examples=12
    )
    test_vectors = []
    for row in range(len(vectors)):
        memory_keys = vectors.memory_keys[row]
        query = int(vectors.queries[row])
        scores = key_weights[memory_keys].astype(np.int64) @ query_weights[
            query
        ].astype(np.int64)
        winner = int(np.argmax(scores))
        test_vectors.append(
            {
                "memory_keys": memory_keys.tolist(),
                "memory_values": vectors.memory_values[row].tolist(),
                "query": query,
                "scores": scores.tolist(),
                "winner": winner,
                "result": int(vectors.memory_values[row, winner]),
            }
        )

    include = [
        "; Generated EXP-011 model and demo contexts. Do not edit.",
        f"ATT_KEY_COUNT       equ     {KEY_COUNT}",
        f"ATT_VALUE_COUNT     equ     {VALUE_COUNT}",
        f"ATT_MEMORY_SIZE     equ     {MEMORY_SIZE}",
        f"ATT_WIDTH           equ     {WIDTH}",
        f"ATT_CONTEXT_COUNT   equ     {len(DEMO_CONTEXTS)}",
        f"ATT_MODEL_ID        equ     ${model_id:04x}",
        "",
        *fcb_lines("attention_query_weights", query_weights),
        "",
        *fcb_lines("attention_key_weights", key_weights),
        "",
        *fcb_lines("attention_demo_contexts", contexts),
        "",
    ]
    manifest = {
        "experiment": 11,
        "training_seed": TRAINING_SEED,
        "model_seed": MODEL_SEED,
        "training_examples": TRAINING_EXAMPLES,
        "epochs": EPOCHS,
        "key_count": KEY_COUNT,
        "value_count": VALUE_COUNT,
        "memory_size": MEMORY_SIZE,
        "width": WIDTH,
        "fractional_bits": FRACTIONAL_BITS,
        "parameters": len(weights),
        "model_id": f"{model_id:04X}",
        "query_weights": query_weights.astype(int).tolist(),
        "key_weights": key_weights.astype(int).tolist(),
        "demo_contexts": [
            {"keys": list(keys), "values": list(values)}
            for keys, values in DEMO_CONTEXTS
        ],
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "attention_data.inc").write_text("\n".join(include), encoding="ascii")
    (OUTPUT / "weights.bin").write_bytes(weights)
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (OUTPUT / "test-vectors.json").write_text(
        json.dumps(test_vectors, indent=2) + "\n", encoding="utf-8"
    )
    print(f"model {model_id:04X}: {len(weights)} signed Q4.4 parameter bytes")
    print(f"wrote {OUTPUT / 'attention_data.inc'}")


if __name__ == "__main__":
    main()
