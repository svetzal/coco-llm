#!/usr/bin/env python3
"""EXP-010 Phase A: does the melody model beat a memory-matched table?

Trains the model and interpolated backoff tables on the chorale corpus and
compares held-out cross-entropy in bits per row. Also runs the two checks that
EXP-008 showed were not optional: a negative control on a shuffled corpus, and
a split of the model's advantage by whether the context was ever seen in
training, since generalization to unseen contexts is the mechanism claimed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from melody_lm import (
    ALL_FEATURES,
    PAD,
    MelodyConfig,
    MelodyModel,
    TableBaseline,
    UniformBaseline,
    build_examples,
)
from melody_tokens import MELODY_TOKENS, Tune

DEFAULT_CORPUS = ROOT / "experiments" / "data" / "EXP-010-chorales.jsonl"
REQUIRED_MARGIN = 0.15
NOISE_MARGIN = 0.05


def load(path: Path) -> tuple[list[Tune], list[Tune]]:
    train, holdout = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        (holdout if payload["split"] == "holdout" else train).append(
            Tune.from_json(payload)
        )
    return train, holdout


def shuffled(tunes: list[Tune], seed: int) -> list[Tune]:
    """Tokens pooled across the whole corpus and redealt.

    Shuffling within a tune is not enough. It preserves that tune's own token
    distribution, and eighteen rows of history reveal it, so the model
    legitimately beats a global unigram and the control trips for a reason
    that is not a fault. Pooling first removes per-tune structure as well, and
    then nothing above the global unigram should be learnable.
    """
    random = np.random.Generator(np.random.PCG64(seed))
    pool = [token for tune in tunes for token in tune.melody]
    random.shuffle(pool)
    cursor = 0
    out = []
    for tune in tunes:
        melody = pool[cursor : cursor + tune.rows]
        cursor += tune.rows
        out.append(
            Tune(
                source=tune.source,
                title=tune.title,
                mode=tune.mode,
                metre=tune.metre,
                tonic=tune.tonic,
                melody=tuple(melody),
                chords=tune.chords,
                beats=tune.beats,
            )
        )
    return out


def seen_contexts(tunes: list[Tune], history: int) -> set[tuple[int, ...]]:
    seen = set()
    for tune in tunes:
        window = [PAD] * history
        for row in range(tune.rows):
            seen.add(tuple(window))
            window = window[1:] + [tune.melody[row]]
    return seen


def split_by_novelty(
    model: MelodyModel,
    tunes: list[Tune],
    config: MelodyConfig,
    seen: set[tuple[int, ...]],
) -> tuple[float, float, int, int]:
    contexts, targets = build_examples(tunes, config)
    log_probabilities = model.log_softmax(model.logits(contexts))
    bits = -log_probabilities[np.arange(len(targets)), targets] / np.log(2.0)

    offset = len(config.features)
    novel = np.array([tuple(row[offset:]) not in seen for row in contexts], dtype=bool)
    known = ~novel
    return (
        float(bits[known].mean()) if known.any() else float("nan"),
        float(bits[novel].mean()) if novel.any() else float("nan"),
        int(known.sum()),
        int(novel.sum()),
    )


def table_bits_by_novelty(table, tunes, config, seen) -> tuple[float, float]:
    """Table cross-entropy split the same way as the model's, row for row."""
    known_total = known = novel_total = novel = 0.0, 0, 0.0, 0
    known_total, known, novel_total, novel = 0.0, 0, 0.0, 0
    for tune in tunes:
        window = [PAD] * config.history
        for row in range(tune.rows):
            bits = -np.log2(
                max(
                    table.distribution(window[-2:], tune.chords[row])[tune.melody[row]],
                    1e-12,
                )
            )
            if tuple(window) in seen:
                known_total += bits
                known += 1
            else:
                novel_total += bits
                novel += 1
            window = window[1:] + [tune.melody[row]]
    return (
        known_total / max(1, known),
        novel_total / max(1, novel),
    )


def train_model(train: list[Tune], config: MelodyConfig, epochs: int) -> MelodyModel:
    contexts, targets = build_examples(train, config)
    model = MelodyModel(config)
    model.train(contexts, targets, epochs=epochs)
    return model


def evaluate(model: MelodyModel, tunes: list[Tune], config: MelodyConfig) -> float:
    contexts, targets = build_examples(tunes, config)
    return model.bits_per_row(contexts, targets)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    # 10 epochs leaves the model far short of convergence: it scores 1.690 bits
    # there and 1.140 by 80. An early sweep at 10 nearly produced a null result
    # against a model that had not finished training.
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--histories", type=str, default="4,10,18")
    parser.add_argument("--embeddings", type=str, default="6,8")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    train, holdout = load(arguments.corpus)
    histories = [int(v) for v in arguments.histories.split(",")]
    embeddings = [int(v) for v in arguments.embeddings.split(",")]

    print("EXP-010 Phase A: melody continuation")
    print(f"train {len(train)} tunes, holdout {len(holdout)} tunes")
    print(f"melody vocabulary {MELODY_TOKENS}, epochs {arguments.epochs}")
    print()

    uniform = UniformBaseline()
    print(f"{'method':<34}{'params/bytes':>14}{'holdout bits':>14}")
    print(f"  {'uniform':<32}{'-':>14}{uniform.bits:>13.3f}")

    best_table, best_table_name = None, ""
    for order in (1, 2):
        for by_chord in (False, True):
            table = TableBaseline(order, by_chord=by_chord)
            table.fit(train, order)
            bits = table.bits_per_row(holdout, order)
            name = f"table/order{order}" + ("/chord" if by_chord else "")
            print(f"  {name:<32}{table.contexts_seen:>14}{bits:>13.3f}")
            if best_table is None or bits < best_table:
                best_table, best_table_name = bits, name

    print()
    best_model, best_model_name, best_config = None, "", None
    for features in (ALL_FEATURES, ()):
        for history in histories:
            for embedding in embeddings:
                config = MelodyConfig(
                    history=history, embedding=embedding, features=features
                )
                if config.parameters > 4096:
                    continue
                model = train_model(train, config, arguments.epochs)
                bits = evaluate(model, holdout, config)
                tag = "situational" if features else "history"
                name = f"model/{tag}/H{history}/E{embedding}"
                print(f"  {name:<32}{config.parameters:>14}{bits:>13.3f}")
                if best_model is None or bits < best_model:
                    best_model, best_model_name, best_config = bits, name, config

    margin = best_table - best_model
    print()
    print(f"best table  {best_table:.3f} bits  ({best_table_name})")
    print(f"best model  {best_model:.3f} bits  ({best_model_name})")
    print(f"margin      {margin:+.3f} bits")
    print()

    model = train_model(train, best_config, arguments.epochs)
    seen = seen_contexts(train, best_config.history)
    known_bits, novel_bits, known, novel = split_by_novelty(
        model, holdout, best_config, seen
    )
    table = TableBaseline(2, by_chord=True)  # the strongest baseline
    table.fit(train, 2)
    table_known, table_novel = table_bits_by_novelty(table, holdout, best_config, seen)
    print("Advantage by context novelty (model vs table, same rows)")
    print(f"  {'bucket':<22}{'rows':>8}{'model':>9}{'table':>9}{'margin':>9}")
    print(
        f"  {'seen in training':<22}{known:>8}{known_bits:>9.3f}"
        f"{table_known:>9.3f}{table_known - known_bits:>+9.3f}"
    )
    print(
        f"  {'never seen':<22}{novel:>8}{novel_bits:>9.3f}"
        f"{table_novel:>9.3f}{table_novel - novel_bits:>+9.3f}"
    )

    # Shuffling destroys order but preserves each tune's token distribution,
    # so the reference is a unigram fitted to the same shuffled data, not the
    # uniform floor. Comparing against uniform made this trip spuriously.
    shuffled_train = shuffled(train, 5)
    shuffled_holdout = shuffled(holdout, 7)
    control = train_model(shuffled_train, best_config, arguments.epochs)
    control_bits = evaluate(control, shuffled_holdout, best_config)
    unigram = TableBaseline(0)
    unigram.fit(shuffled_train, 0)
    unigram_bits = unigram.bits_per_row(shuffled_holdout, 0)
    print()
    print(
        f"negative control (shuffled)      {control_bits:.3f} bits "
        f"vs unigram {unigram_bits:.3f}"
    )

    print()
    print("Phase A gates")
    print(
        f"  {'PASS' if margin >= REQUIRED_MARGIN else 'FAIL'}  "
        f"model beats best table by >={REQUIRED_MARGIN} bits ({margin:+.3f})"
    )
    print(
        f"  {'PASS' if best_config.parameters <= 4096 else 'FAIL'}  "
        f"selected candidate {best_config.parameters} parameters"
    )
    control_gap = unigram_bits - control_bits
    print(
        f"  {'PASS' if control_gap <= NOISE_MARGIN else 'FAIL'}  "
        f"negative control within {NOISE_MARGIN} bits of unigram "
        f"({control_gap:+.3f})"
    )


if __name__ == "__main__":
    main()
