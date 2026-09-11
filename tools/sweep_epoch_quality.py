#!/usr/bin/env python3
"""Was twenty epochs the right place to stop?

EXP-002 picked twenty and the deck shows twenty, and neither had measured
whether it was a good choice or a comfortable one. The obvious intuition is
that more training would make the generated names more recognizable, so this
sweeps the run and measures two things at each point, over 200 samples:

  new         the generated name is not in the training corpus
  like a name EXP-002's rubric, written before any sample was seen: two to
              four tokens, first token a manufacturer that starts a real name

Neither alone is the quantity of interest. Novelty on its own rewards the
untrained model, which invents constantly and never produces a name.
Name-likeness on its own peaks when the model recites the corpus back, because
real names are trivially name-like. The measure that matters is both at once.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from token_lm import (
    ModelConfig,
    TokenLanguageModel,
    assess_samples,
    build_vocabulary,
    load_names,
    make_examples,
)

CORPUS = ROOT / "experiments" / "data" / "EXP-002-tokenized-computer-names.txt"
LEARNING_RATE = 1 / 16
SAMPLES = 200
POINTS = (0, 1, 2, 3, 5, 8, 10, 13, 15, 18, 20, 25, 30, 35, 40, 50, 60, 80, 120)


def main() -> None:
    names = load_names(CORPUS)
    vocabulary, by_text = build_vocabulary(names)
    config = ModelConfig()
    contexts, targets = make_examples(names, by_text, config.context)
    model = TokenLanguageModel(config, vocabulary)

    print(f"{'epoch':>6}{'loss':>9}{'new':>7}{'like a name':>13}{'both':>7}")
    best = (-1, -1)
    for epoch in range(max(POINTS) + 1):
        if epoch:
            model.train(contexts, targets, epochs=1, learning_rate=LEARNING_RATE)
        if epoch not in POINTS:
            continue
        drawn = [
            model.generate(temperature=0.7, random_seed=config.seed + n)
            for n in range(SAMPLES)
        ]
        assessed = assess_samples(drawn, names)
        new = sum(a.novel for a in assessed)
        like = sum(a.name_like for a in assessed)
        both = sum(a.novel and a.name_like for a in assessed)
        if both > best[0]:
            best = (both, epoch)
        print(
            f"{epoch:>6}{model.loss(contexts, targets):>9.3f}"
            f"{100 * new // SAMPLES:>6}%{100 * like // SAMPLES:>12}%"
            f"{100 * both // SAMPLES:>6}%"
        )
    print(f"\nbest at epoch {best[1]}, {100 * best[0] // SAMPLES}% both")


if __name__ == "__main__":
    main()
