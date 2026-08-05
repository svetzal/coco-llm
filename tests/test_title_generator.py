"""The generated titles must read as English, and must not be real episodes.

Both are properties of the whole pipeline rather than of any one function, so
these run the real thing - the trained integer model, the observed-transition
mask, the tagged lexicon - and assert over what comes out. A screen of titles
is the deliverable; these are the checks that it is worth showing.
"""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))
sys.path.insert(0, str(ROOT / "tools"))

from fixed_token_lm import XorShift16
from measure_tos_tokenizations import as_slotted, entities
from run_exp_012 import build, generate
from title_generator import (
    NM,
    NPL,
    NS,
    PN,
    SLOT,
    Entity,
    load_lexicon,
    render,
    slots_of,
    solo_phrases,
    title_hash,
)
from token_lm import BOUNDARY, load_names

CORPUS = ROOT / "experiments" / "data" / "EXP-012-tos-titles.txt"
LEXICON = ROOT / "experiments" / "data" / "EXP-012-tos-lexicon.txt"
SCREEN_COLUMNS = 32


def settings(**overrides) -> Namespace:
    base = {
        "corpus": CORPUS,
        "lexicon": LEXICON,
        "epochs": 60,
        "embedding": 3,
        "context": 2,
        "seed": 6809,
        "titles": 16,
        "min_slots": 2,
        "max_slots": 2,
        "rng_seed": 0x1A2B,
    }
    base.update(overrides)
    return Namespace(**base)


@pytest.fixture(scope="module")
def generator():
    return build(settings())


def screen(generator, rng_seed: int, count: int = 16) -> list[str]:
    model, filler, allowed, _, titles, _ = generator
    random = XorShift16(rng_seed)
    forbidden = {title_hash(title) for title in titles}
    produced = []
    for _ in range(count):
        title = generate(model, filler, allowed, random, forbidden)
        if title is not None:
            produced.append(title)
            forbidden.add(title_hash(title))
    return produced


def test_a_full_screen_is_produced(generator) -> None:
    """A gap on the screen is a visible failure, so the budget must suffice."""
    assert len(screen(generator, 0x1A2B)) == 16


def test_titles_fit_the_coco_screen(generator) -> None:
    for title in screen(generator, 0x1A2B):
        assert len(title) <= SCREEN_COLUMNS, title


def test_no_real_episode_is_ever_emitted(generator) -> None:
    """It is a fake title generator; emitting a real one is the whole failure."""
    known = set(load_names(CORPUS))
    for seed in (0x1A2B, 0x7C41, 0x0005, 0xBEEF):
        for title in screen(generator, seed):
            assert title not in known, title


def test_a_screen_never_repeats_itself(generator) -> None:
    for seed in (0x1A2B, 0x7C41, 0xBEEF):
        produced = screen(generator, seed)
        assert len(set(produced)) == len(produced)


def test_the_same_seed_gives_the_same_screen(generator) -> None:
    """The CoCo has to reproduce this stream exactly, so it must be a stream."""
    assert screen(generator, 0x1A2B) == screen(generator, 0x1A2B)


# Stated here rather than imported, so this asserts English rather than
# asserting that title_generator agrees with itself. An earlier version read
# AFTER_DETERMINER and passed happily when that table was mutated to permit
# "THE GOTHOS".
FORBIDDEN_AFTER = {
    "THE": (PN,),  # THE GOTHOS
    "A": (NM, NPL, PN),  # A TRIBBLES
    "AN": (NM, NPL, PN),
    "THIS": (NPL, PN),  # THIS TRIBBLES
    "OUR": (NS, NM, PN),  # OUR MERCY
    "IS": (NS, NM, NPL),  # REQUIEM IS NAKED TIME
}
# A preposition standing on its own needs a noun that does not want an
# article: "OF MERCY" and "OF GOTHOS" are fine, "OF SQUIRE" is not.
PREPOSITIONS = ("OF", "TO", "WITH", "FOR", "AND", "IN", "ON")


def slot_neighbours(title: str, phrases: list[str]) -> list[tuple[str | None, str]]:
    """Split a rendered title back into (word before, noun phrase) pairs."""
    found: list[tuple[int, str]] = []
    remaining = title
    for phrase in phrases:
        index = remaining.find(phrase)
        if index < 0:
            continue
        found.append((index, phrase))
        remaining = (
            remaining[:index] + "\0" * len(phrase) + remaining[index + len(phrase) :]
        )
    pairs = []
    for index, phrase in sorted(found):
        before = title[:index].replace("\0", " ").split()
        pairs.append((before[-1] if before else None, phrase))
    return pairs


def test_determiners_agree_with_the_nouns_they_take(generator) -> None:
    """ "A TRIBBLES" and "THE GOTHOS" are what the tags exist to prevent."""
    _, _, _, lexicon, _, _ = generator
    tag_of = {entity.text: entity.tag for entity in lexicon}
    phrases = sorted(tag_of, key=len, reverse=True)

    checked = 0
    for seed in (0x1A2B, 0x7C41, 0x0005, 0xBEEF):
        for title in screen(generator, seed):
            for preceding, phrase in slot_neighbours(title, phrases):
                checked += 1
                banned = FORBIDDEN_AFTER.get(preceding, ())
                assert tag_of[phrase] not in banned, (
                    f"{title!r}: {preceding} {phrase} is {tag_of[phrase]}"
                )
                if preceding in PREPOSITIONS:
                    assert tag_of[phrase] != NS, f"{title!r}: {preceding} {phrase}"
    # A split that silently matched nothing would pass every assertion above.
    assert checked >= 100


def test_generated_frames_use_only_observed_transitions(generator) -> None:
    """The mask is what stopped "TRISKELION THE MAN TRAP" reaching the screen."""
    model, _, allowed, _, _, facts = generator
    index_of = model.token_by_text
    for frame in facts["frames"]:
        previous = index_of[BOUNDARY]
        for token in frame.split():
            assert index_of[token] in allowed[previous]
            previous = index_of[token]


def test_one_slot_frames_cannot_produce_a_novel_title() -> None:
    """Why min_slots is 2. This is a property of the corpus, not a preference.

    Every noun the corpus is willing to build a whole title from is a noun it
    has already built that exact title from, so a one-slot frame reproduces an
    episode rather than inventing one.
    """
    titles = load_names(CORPUS)
    known = set(titles)
    solo = solo_phrases(titles, as_slotted, entities)
    for preceding, phrases in solo.items():
        for phrase in phrases:
            rebuilt = f"{preceding} {phrase}" if preceding else phrase
            if rebuilt not in known:
                # Only the frames over dropped verb phrases escape, and those
                # are not in the lexicon to be drawn anyway.
                assert preceding in {"ARE", "I", "OTHER", "OUR", "WHICH"}


def test_article_follows_the_word_it_precedes() -> None:
    frame = ["A", SLOT, "OF", SLOT]
    assert render(frame, [Entity(NS, "EYE"), Entity(NS, "GUN")]).startswith("AN EYE")
    assert render(frame, [Entity(NS, "GUN"), Entity(NS, "EYE")]).startswith("A GUN")


def test_a_slot_knows_both_of_its_neighbours() -> None:
    assert slots_of(["THE", SLOT, "IS", SLOT]) == [("THE", "IS"), ("IS", None)]


def test_every_lexicon_phrase_is_printable_on_a_coco() -> None:
    for entity in load_lexicon(LEXICON):
        assert entity.text.isascii()
        assert entity.text == entity.text.upper()


def test_plural_nouns_are_tagged_as_plural() -> None:
    """A spot check that the hand tagging is not arbitrary."""
    tags = {entity.text: entity.tag for entity in load_lexicon(LEXICON)}
    assert tags["TRIBBLES"] == NPL
    assert tags["CAGE"] == NS
