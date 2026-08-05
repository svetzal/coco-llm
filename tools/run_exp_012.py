#!/usr/bin/env python3
"""Train the EXP-012 frame model on the Mac and generate fake episode titles.

The model learns title *grammar* - the closed-class scaffolding a Star Trek
title hangs on - and nothing else. Nouns are drawn from a tagged table. See
src/reference/title_generator.py for why the corpus is split that way.

Everything here is the integer model the CoCo runs: Q4.12 masters consumed as
Q4.4, byte probabilities, and an XorShift16 drawn from for both the frame
tokens and the slot fills, so the 6809 reproduces this stream exactly.

Reports the shipped size, which is the number that decides whether the demo is
possible at all.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))
sys.path.insert(0, str(ROOT / "tools"))

from fixed_token_lm import FixedTokenLanguageModel, XorShift16
from measure_tos_tokenizations import as_slotted, entities
from title_generator import (
    SLOT,
    Entity,
    SlotFiller,
    draw_below,
    generate_frame,
    initial_phrases,
    is_fillable,
    load_lexicon,
    render,
    title_hash,
    transition_mask,
)
from token_lm import BOUNDARY, ModelConfig, load_names, make_examples

DEFAULT_CORPUS = ROOT / "experiments" / "data" / "EXP-012-tos-titles.txt"
DEFAULT_LEXICON = ROOT / "experiments" / "data" / "EXP-012-tos-lexicon.txt"
SCREEN_COLUMNS = 32
MAX_FRAME_TOKENS = 8


def trainable_frames(titles, lexicon: list[Entity]):
    """Frames whose every slot the tagged lexicon can actually fill.

    A title like "Whom Gods Destroy" slots to `WHOM <X>` over a verb phrase.
    Keeping it would teach the model a frame whose slot only nouns are
    available for, and the generator would emit "WHOM TRIBBLES".
    """
    known = {entity.text for entity in lexicon}
    kept, dropped = [], Counter()
    for title in titles:
        frame = as_slotted(title)
        if not all(phrase in known for phrase in entities(title)):
            dropped["entity not in lexicon"] += 1
            continue
        if not is_fillable(frame, lexicon):
            dropped["slot has no admissible tag"] += 1
            continue
        if len(frame) > MAX_FRAME_TOKENS:
            dropped["frame too long"] += 1
            continue
        kept.append(" ".join(frame))
    return kept, dropped


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--lexicon", type=Path, default=DEFAULT_LEXICON)
    # Eleven, not because it is enough training but because it is as much as
    # the arithmetic survives. model_forward.asm accumulates a logit in D, so
    # it wraps at 16 bits where the reference clamps; at twelve epochs the
    # Q4.12 masters have grown enough to reach that, and the CoCo and the Mac
    # stop agreeing. tools/export_exp_012.py measures the peak and refuses.
    parser.add_argument("--epochs", type=int, default=11)
    # Three matches EMBED_DIMS in src/6809/model_core.asm, so the CoCo runs
    # the existing forward pass unaltered.
    parser.add_argument("--embedding", type=int, default=3)
    parser.add_argument("--context", type=int, default=2)
    parser.add_argument("--seed", type=int, default=6809)
    parser.add_argument("--titles", type=int, default=16)
    parser.add_argument(
        "--max-slots",
        type=int,
        default=2,
        help="reject frames with more slots. The transition mask is a bigram "
        "rule, so it happily chains 'THE MAN TO GIDEON TO ELAAN'; the corpus "
        "uses three slots exactly once in 79 titles.",
    )
    parser.add_argument(
        "--min-slots",
        type=int,
        default=2,
        help="reject frames with fewer slots. Two is forced, not chosen: all 39 "
        "nouns the corpus lets carry a title alone reconstruct their own real "
        "episode, so a one-slot frame cannot produce a novel title at all.",
    )
    parser.add_argument("--rng-seed", type=lambda t: int(t, 0), default=0x1A2B)
    return parser.parse_args()


def build(arguments):
    titles = load_names(arguments.corpus)
    lexicon = load_lexicon(arguments.lexicon)
    frames, dropped = trainable_frames(titles, lexicon)

    vocabulary = [BOUNDARY] + sorted({t for f in frames for t in f.split()})
    token_by_text = {text: index for index, text in enumerate(vocabulary)}
    config = ModelConfig(
        context=arguments.context, embedding=arguments.embedding, seed=arguments.seed
    )
    contexts, targets = make_examples(frames, token_by_text, config.context)
    model = FixedTokenLanguageModel(config, vocabulary)
    initial = model.loss(contexts, targets)
    losses = model.train(contexts, targets, epochs=arguments.epochs)

    facts = {
        "slotting": (as_slotted, entities),
        "titles": titles,
        "frames": frames,
        "dropped": dropped,
        "losses": losses,
        "initial": initial,
        "examples": len(targets),
    }
    allowed = transition_mask([f.split() for f in frames], vocabulary)
    opening = initial_phrases(titles, as_slotted, entities)
    return model, SlotFiller(lexicon, opening), allowed, lexicon, titles, facts


def generate(
    model, filler, allowed, random, forbidden, *, min_slots=2, max_slots=2, attempts=120
) -> str | None:
    """One title: a frame from the model, then nouns that fit its slots."""
    for _ in range(attempts):
        frame = generate_frame(model, allowed, random, limit=MAX_FRAME_TOKENS)
        if not min_slots <= frame.count(SLOT) <= max_slots:
            continue
        choices = filler.fill(frame, lambda n: draw_below(random, n))
        if choices is None:
            continue
        title = render(frame, choices)
        if len(title) <= SCREEN_COLUMNS and title_hash(title) not in forbidden:
            return title
    return None


def main() -> None:
    arguments = parse_arguments()
    model, filler, allowed, lexicon, titles, facts = build(arguments)

    print(f"frames trained on : {len(facts['frames'])} of {len(titles)} titles")
    for reason, count in facts["dropped"].most_common():
        print(f"  dropped {count:>3}  {reason}")
    print(f"frame vocabulary  : {model.vocabulary_size} tokens")
    print(f"lexicon           : {len(lexicon)} tagged noun phrases")
    print(
        f"loss              : {facts['initial']:.4f} -> "
        f"{facts['losses'][-1]:.4f} over {arguments.epochs} epochs "
        f"({facts['examples']} examples)"
    )
    print()

    parameters = model.parameter_count
    spelling = sum(len(entity.text) + 1 for entity in lexicon)
    tags = len(lexicon)
    words = sum(len(token) + 1 for token in model.vocabulary if token != BOUNDARY)
    print("shipped size, one byte per Q4.4 parameter")
    print(f"  model parameters  {parameters:>6}")
    print(f"  frame word table  {words:>6}")
    print(f"  noun phrases      {spelling:>6}")
    print(f"  noun tags         {tags:>6}")
    print(f"  total             {parameters + words + spelling + tags:>6} bytes")
    print()

    random = XorShift16(arguments.rng_seed)
    known = set(titles)
    forbidden = {title_hash(title) for title in titles}
    # A screen that shows SAVAGE CURTAIN twice reads as a bug, so each title
    # joins the reject set as it lands. Two bytes per row on the CoCo.
    produced = []
    seen = set(forbidden)
    for _ in range(arguments.titles):
        title = generate(
            model,
            filler,
            allowed,
            random,
            seen,
            min_slots=arguments.min_slots,
            max_slots=arguments.max_slots,
        )
        produced.append(title)
        if title:
            seen.add(title_hash(title))
    print(f"{arguments.titles} titles, as they would fill the screen")
    print("  " + "-" * SCREEN_COLUMNS)
    for title in produced:
        if title is None:
            print("  <no title within the attempt budget>")
            continue
        mark = "  (real episode)" if title in known else ""
        print(f"  {title}{mark}")
    print("  " + "-" * SCREEN_COLUMNS)

    made = [title for title in produced if title]
    real = sum(1 for title in made if title in known)
    print(f"{len(made)}/{arguments.titles} produced, {real} of them real episodes")
    print(f"longest {max(len(t) for t in made)} of {SCREEN_COLUMNS} columns")


if __name__ == "__main__":
    main()
