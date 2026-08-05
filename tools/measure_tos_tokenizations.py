#!/usr/bin/env python3
"""Does treating entities as units make the title corpus learnable?

EXP-012 measured a corpus where almost nothing repeats: 174 distinct adjacent
word pairs out of 180 instances. A model with a two-word context sees each of
its transitions once and can only memorize.

The proposal under test is to stop spending three tokens on "SQUIRE OF GOTHOS".
Three ways to do that are compared, because they are not the same idea and only
one of them addresses the problem:

  words     the baseline: one token per whitespace-separated word.
  merged    "SQUIRE OF GOTHOS" becomes one token, swallowing the OF. Fewer,
            longer tokens. This is the proposal read literally.
  slotted   "SQUIRE OF GOTHOS" becomes "<X> OF <X>": the entity phrases are
            lifted out into a separate lexicon and the title keeps only its
            frame. This spends MORE structure on the frame, not less.

The number to watch is not vocabulary or bytes. It is the share of adjacent
pairs that occur more than once, because that is the evidence a next-token
model has to generalize from. Merging barely moves it. Slotting transforms it.

The frame-word list below is hand-authored and the slotted result depends on
it. It is a closed-class list - articles, prepositions, auxiliaries,
determiners - chosen for being the words that recur across unrelated titles.
It is a design decision, not a measurement, and is stated here so the reader
can disagree with it.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from token_lm import load_names

DEFAULT_CORPUS = ROOT / "experiments" / "data" / "EXP-012-tos-titles.txt"
SLOT = "<X>"
PUNCTUATION = "?!:,."

DETERMINERS = {
    "THE",
    "A",
    "AN",
    "THIS",
    "THESE",
    "THAT",
    "ANY",
    "ALL",
    "SOME",
    "EVERY",
    "LAST",
    "OTHER",
    "NO",
    "NOT",
    "THERE",
}
PREPOSITIONS = {
    "OF",
    "IN",
    "ON",
    "AT",
    "TO",
    "FOR",
    "AND",
    "OR",
    "BUT",
    "WITH",
    "BY",
    "FROM",
    "INTO",
}
PRONOUNS = {
    "WHICH",
    "WHO",
    "WHOM",
    "WHAT",
    "WHERE",
    "WHEN",
    "WHOSE",
    "I",
    "MY",
    "YOUR",
    "OUR",
    "THEIR",
    "ITS",
}
AUXILIARIES = {
    "IS",
    "ARE",
    "WAS",
    "WERE",
    "HAS",
    "HAVE",
    "HAD",
    "SHALL",
    "WILL",
    "DO",
    "DOES",
    "BE",
    "BEEN",
    "AM",
}
FRAME = DETERMINERS | PREPOSITIONS | PRONOUNS | AUXILIARIES
# Frame words a merged entity is allowed to swallow when content sits on both
# sides of them, so "TASTE OF ARMAGEDDON" stays one thing.
GLUE = {"OF", "THE", "IN", "ON", "AND"}


def bare(word: str) -> str:
    return word.strip(PUNCTUATION)


def as_words(title: str) -> list[str]:
    return title.split()


def as_merged(title: str) -> list[str]:
    words = title.split()
    out: list[str] = []
    run: list[str] = []
    for index, word in enumerate(words):
        following = words[index + 1] if index + 1 < len(words) else ""
        glued = (
            bare(word) in GLUE and run and following and bare(following) not in FRAME
        )
        if bare(word) not in FRAME or glued:
            run.append(word)
            continue
        if run:
            out.append(" ".join(run))
            run = []
        out.append(word)
    if run:
        out.append(" ".join(run))
    return out


def as_slotted(title: str) -> list[str]:
    out: list[str] = []
    pending = False
    for word in title.split():
        if bare(word) in FRAME:
            if pending:
                out.append(SLOT)
                pending = False
            out.append(bare(word))
        else:
            pending = True
    if pending:
        out.append(SLOT)
    return out


def entities(title: str) -> list[str]:
    """The phrases that as_slotted lifts out into the lexicon."""
    found: list[str] = []
    run: list[str] = []
    for word in title.split():
        if bare(word) in FRAME:
            if run:
                found.append(" ".join(run))
                run = []
        else:
            run.append(word)
    if run:
        found.append(" ".join(run))
    return found


def report(label: str, sequences: list[list[str]]) -> None:
    tokens = [token for sequence in sequences for token in sequence]
    vocabulary = sorted(set(tokens))
    pairs = Counter((a, b) for sequence in sequences for a, b in pairwise(sequence))
    instances = sum(pairs.values())
    repeated = 1 - len(pairs) / instances if instances else 0.0
    # One boundary token, plus embedding, output weights and bias per token.
    size = len(vocabulary) + 1
    parameters = size * 10
    spelling = sum(len(entry) + 1 for entry in vocabulary)
    print(
        f"  {label:<9} {size:>6} {len(tokens):>7} {len(tokens) / len(sequences):>7.1f}"
        f" {len(pairs):>4}/{instances:<4} {100 * repeated:>8.0f}%"
        f" {parameters + spelling:>7}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--show", type=int, default=8, help="example titles")
    arguments = parser.parse_args()

    titles = load_names(arguments.corpus)

    print(f"{len(titles)} titles from {arguments.corpus.relative_to(ROOT)}")
    print()
    print(
        f"  {'scheme':<9} {'vocab':>6} {'tokens':>7} {'len':>7} "
        f"{'bigrams':>9} {'repeated':>9} {'bytes':>7}"
    )
    report("words", [as_words(title) for title in titles])
    report("merged", [as_merged(title) for title in titles])
    report("slotted", [as_slotted(title) for title in titles])

    print()
    print("what each scheme does to the same titles")
    for title in titles[: arguments.show]:
        print(f"  {title}")
        for label, scheme in (("merged", as_merged), ("slotted", as_slotted)):
            print(f"      {label:<8} " + " | ".join(scheme(title)))

    frames = Counter(tuple(as_slotted(title)) for title in titles)
    reused = sum(count for count in frames.values() if count > 1)
    print()
    print(
        f"frames: {len(frames)} distinct over {len(titles)} titles; "
        f"{reused} titles use a frame seen more than once"
    )
    for frame, count in frames.most_common(10):
        print(f"  {count:>3}x  {' '.join(frame)}")

    lexicon = [phrase for title in titles for phrase in entities(title)]
    print()
    print(
        f"lexicon lifted out: {len(lexicon)} phrases, "
        f"{len(set(lexicon))} distinct, "
        f"{sum(len(p) + 1 for p in set(lexicon))} bytes to spell"
    )
    duplicated = [p for p, n in Counter(lexicon).items() if n > 1]
    print(f"  reused across titles: {duplicated or 'none'}")


if __name__ == "__main__":
    main()
