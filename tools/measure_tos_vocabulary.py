#!/usr/bin/env python3
"""How many words does a Star Trek title model need to know?

"Vocabulary" here is not a linguistic count. It is the number of distinct
tokens the model must carry an embedding row and an output row for, so it
sets the parameter count, the spelling table, and therefore whether the thing
fits in a CoCo at all. It is measured with the same splitter the trainer uses
rather than a tidier one, so the number reported is the number that will be
paid for.

Three things are worth knowing beyond the raw count:

  coverage     how much of the corpus the commonest words account for. A
               vocabulary can often be halved by capping the tail, at the
               price of not being able to say the capped words at all.
  hapax        words used exactly once. In a corpus this small they are the
               majority, and each one costs a full row to be usable in
               precisely one title. They are what a vocabulary cap removes.
  cost         bytes, split into the parameters and the spelling table. The
               spelling table is easy to forget and here it is the larger of
               the two.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from token_lm import ModelConfig, build_vocabulary, load_names

DEFAULT_CORPUS = ROOT / "experiments" / "data" / "EXP-012-tos-titles.txt"


def parameter_count(vocabulary: int, config: ModelConfig) -> int:
    """Embedding rows, output weights, output biases."""
    embeddings = vocabulary * config.embedding
    weights = vocabulary * config.context * config.embedding
    return embeddings + weights + vocabulary


def spelling_bytes(words: list[str]) -> int:
    """The table the CoCo prints from: the letters, plus a terminator each."""
    return sum(len(word) + 1 for word in words)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--context", type=int, default=ModelConfig.context)
    parser.add_argument("--embedding", type=int, default=ModelConfig.embedding)
    arguments = parser.parse_args()

    config = ModelConfig(context=arguments.context, embedding=arguments.embedding)
    titles = load_names(arguments.corpus)
    vocabulary, _ = build_vocabulary(titles)
    words = [token for title in titles for token in title.split()]
    counts = Counter(words)

    # build_vocabulary prepends the boundary marker, which is a real token
    # with real rows but has no spelling to print.
    spelled = [token for token in vocabulary if token in counts]

    print(f"corpus  {arguments.corpus.relative_to(ROOT)}")
    print(f"  titles        {len(titles)}")
    print(f"  word tokens   {len(words)}")
    print(f"  per title     {len(words) / len(titles):.1f}")
    print(f"  longest       {max(len(t.split()) for t in titles)} words")
    print()
    print(
        f"vocabulary      {len(vocabulary)} tokens ({len(spelled)} words + 1 boundary)"
    )

    once = [word for word, n in counts.items() if n == 1]
    print(
        f"  used once     {len(once)} ({100 * len(once) / len(spelled):.0f}% "
        f"of the words, {100 * len(once) / len(words):.0f}% of the corpus)"
    )
    print(
        "  commonest     "
        + ", ".join(f"{word} x{n}" for word, n in counts.most_common(8))
    )
    print()

    print("coverage of the corpus by the commonest words")
    ordered = [n for _, n in counts.most_common()]
    running, marks = 0, {}
    for index, n in enumerate(ordered, start=1):
        running += n
        share = running / len(words)
        for target in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
            if target not in marks and share >= target:
                marks[target] = index
    for target, index in sorted(marks.items()):
        print(
            f"  {100 * target:>3.0f}%  {index:>4} words  "
            f"(+1 boundary = {index + 1} tokens)"
        )
    print()

    print(f"cost at context={config.context}, embedding={config.embedding}")
    print(
        f"  {'vocab':>6} {'params':>7} {'Q4.4 bytes':>11} {'spelling':>9} {'total':>7}"
    )
    for target in sorted(marks):
        keep = [word for word, _ in counts.most_common(marks[target])]
        size = len(keep) + 1
        params = parameter_count(size, config)
        spelling = spelling_bytes(keep)
        label = f"{100 * target:.0f}%"
        print(
            f"  {size:>6} {params:>7} {params:>11} {spelling:>9} "
            f"{params + spelling:>7}   {label} coverage"
        )


if __name__ == "__main__":
    main()
