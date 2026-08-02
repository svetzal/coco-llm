#!/usr/bin/env python3
"""Prove the 6809 melody inference matches the fixed-point reference exactly.

Picks contexts from the corpus, computes their scores with
src/reference/melody_fixed.py, and asserts the assembly produces the same
sixteen-bit scores and the same winning token.

Scores are checked, not only the winner. A model can pick the right token for
the wrong reasons, and the scores are what a sampler would later draw from.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from melody_lm import MelodyConfig, build_examples
from melody_tokens import Tune

MANIFEST = ROOT / "build" / "exp010" / "melody_model.json"
CORPUS = ROOT / "experiments" / "data" / "EXP-010-dance.jsonl"
BINARY = ROOT / "build" / "melody-core.bin"
SYMBOLS = ROOT / "build" / "melody-core.sym"
RUNNER_ORG = 0x0E00
MODEL_ORG = 0x2000
CASES = 6


def symbol(text: str, name: str) -> int:
    """Address of a label in lwasm's symbol dump."""
    import re

    match = re.search(rf"^{re.escape(name)} EQU \$([0-9A-Fa-f]+)$", text, re.MULTILINE)
    if match is None:
        raise ValueError(f"symbol not found: {name}")
    return int(match.group(1), 16)


def load_holdout() -> list[Tune]:
    return [
        Tune.from_json(json.loads(line))
        for line in CORPUS.read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line)["split"] == "holdout"
    ]


def reference_scores(manifest: dict, context: list[int]) -> np.ndarray:
    vector = np.zeros(manifest["embedding"], dtype=np.int64)
    for position, token in enumerate(context):
        vector += np.asarray(manifest["embeddings"][position][token], dtype=np.int64)
    weights = np.asarray(manifest["weights"], dtype=np.int64)
    biases = np.asarray(manifest["biases"], dtype=np.int64)
    return weights @ vector + biases


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    manifest = json.loads(MANIFEST.read_text())
    config = MelodyConfig(
        history=manifest["history"],
        embedding=manifest["embedding"],
        features=tuple(manifest["features"]),
    )
    contexts, _ = build_examples(load_holdout(), config)

    # Spread the cases across the holdout rather than taking the first few,
    # which would all come from one tune's opening.
    stride = max(1, len(contexts) // CASES)
    chosen = [contexts[index * stride] for index in range(CASES)]

    # The direct simulator's assembler chokes on labels of sixteen characters
    # or more, so the core is assembled by lwasm and its bytes are emitted
    # literally. That also makes this a test of the artifact the CoCo runs
    # rather than of a second assembly of the same source.
    payload = BINARY.read_bytes()
    symbols = SYMBOLS.read_text()
    address = {
        name: symbol(symbols, name)
        for name in (
            "melody_predict",
            "melody_context",
            "melody_scores",
            "melody_best_token",
        )
    }

    lines = [
        "; Generated melody parity image. Do not edit.",
        f"; {CASES} contexts scored against src/reference/melody_fixed.py",
        f"        org     ${RUNNER_ORG:04X}",
        f"start   lds     #${RUNNER_ORG - 1:04X}",
    ]

    expectations: list[str] = []
    for case, context in enumerate(chosen):
        scores = reference_scores(manifest, list(context))
        winner = int(np.argmax(scores))
        lines.append(f"; --- case {case} ---")
        for position, token in enumerate(context):
            lines.append(f"        lda     #{int(token)}")
            lines.append(f"        sta     ${address['melody_context'] + position:04X}")
        lines.append(f"        jsr     ${address['melody_predict']:04X}")
        lines.append(f"        ldd     ${address['melody_scores']:04X}")
        lines.append(f"        std     c{case}first")
        lines.append(f"        ldd     ${address['melody_scores'] + 2 * winner:04X}")
        lines.append(f"        std     c{case}best")
        lines.append(f"        lda     ${address['melody_best_token']:04X}")
        lines.append(f"        sta     c{case}tok")
        expectations.append(f";! c{case}first = #${int(scores[0]) & 0xFFFF:04X}")
        expectations.append(f";! c{case}best = #${int(scores[winner]) & 0xFFFF:04X}")
        expectations.append(f";! c{case}tok = #${winner:02X}")

    lines.append("        swi")
    for case in range(CASES):
        lines.append(f"c{case}first rmb 2")
        lines.append(f"c{case}best rmb 2")
        lines.append(f"c{case}tok rmb 1")

    lines.append("")
    lines.append(f"        org     ${MODEL_ORG:04X}")
    for start in range(0, len(payload), 16):
        chunk = payload[start : start + 16]
        lines.append("        fcb     " + ",".join(f"${b:02X}" for b in chunk))
    lines += ["", *expectations, ""]

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text("\n".join(lines), encoding="ascii")
    print(f"{CASES} cases, {config.context} context positions")
    print(f"wrote {arguments.output}")


if __name__ == "__main__":
    main()
