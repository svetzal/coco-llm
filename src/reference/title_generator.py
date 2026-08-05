"""Generate fake Star Trek episode titles that read as English.

EXP-012 measured why the obvious approach fails. Over 79 titles only two
adjacent word pairs ever repeat, so a word-level model has no repeated evidence
and can only reproduce its training data. The corpus splits instead into two
parts that behave completely differently:

  the frame    THE <X> OF THE <X> - closed-class words in a short, heavily
               repeated pattern. 79 titles use only 32 distinct frames and 62%
               of adjacent pairs recur. This is learnable, and it is what the
               model here is trained on.
  the entities SQUIRE, GOTHOS, TRIBBLES - 101 noun phrases with no shared
               structure worth learning. These are a table, not a model.

Novelty comes from recombining the two, which is why the output is new without
the model having to invent English.

Slot filling is grammatical rather than random. Each entity carries a tag - a
count noun, a mass noun, a plural, a proper noun - and the word in front of the
slot decides which tags may fill it. That single rule is what stops the
generator emitting "A TRIBBLES" or "THE GOTHOS", and it is cheap enough to run
on a 6809: one table lookup per slot.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

BOUNDARY = "<END>"
SLOT = "<X>"

NS, NM, NPL, PN = "NS", "NM", "NPL", "PN"
TAGS = (NS, NM, NPL, PN)

# What may follow each determiner. A slot with no word in front of it is a
# title-initial slot, where a bare singular is idiomatic ("Arena", "Obsession")
# even though it would be ungrammatical mid-sentence.
AFTER_DETERMINER = {
    "A": (NS,),
    "AN": (NS,),
    "THE": (NS, NM, NPL),
    "THIS": (NS, NM),
    "THESE": (NPL,),
    "OUR": (NPL,),
    "YOUR": (NS, NM),
    "OTHER": (NS,),
    "ANY": (NS, NM),
    "NO": (NS, NM, NPL),
}
# A copula constrains the noun on *both* sides, which is the one place the
# preceding word is not enough: "THE GUN IS PATTERNS" and "TRIBBLES IS
# BALANCE" are each wrong on the side the other rule does not see.
# The corpus states this frame once, as "Tomorrow Is Yesterday" - two proper
# nouns. Common nouns in it read as a missing article ("REQUIEM IS NAKED
# TIME"), so the single observation is taken at its word.
BEFORE = {"IS": (PN,), "ARE": (NPL,)}
AFTER_DETERMINER["IS"] = (PN,)
AFTER_DETERMINER["ARE"] = (NPL,)
# After a bare preposition or conjunction a determiner-less noun is needed:
# "OF MERCY", "OF TRIBBLES", "OF GOTHOS", but never "OF SQUIRE".
BARE = (NM, NPL, PN)
VOWELS = "AEIOU"


def draw_below(random, count: int) -> int:
    """A number under `count`, by masking and retrying - the 6809 has no divide.

    The same routine serves both draws, so the CoCo needs one copy of it.
    """
    mask = 1
    while mask < count:
        mask = mask * 2 + 1
    for _ in range(16):
        candidate = random.next() & mask
        if candidate < count:
            return candidate
    return count - 1


@dataclass(frozen=True)
class Entity:
    tag: str
    text: str


def load_lexicon(path: Path) -> list[Entity]:
    entities: list[Entity] = []
    for line in path.read_text(encoding="ascii").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        tag, _, text = stripped.partition(" ")
        if tag not in TAGS:
            raise ValueError(f"unknown tag {tag!r} in {path.name}")
        entities.append(Entity(tag, " ".join(text.split())))
    return entities


def allowed_tags(
    preceding: str | None, following: str | None = None
) -> tuple[str, ...]:
    """Which entity tags may fill a slot, given the words either side of it."""
    tags = TAGS if preceding is None else AFTER_DETERMINER.get(preceding, BARE)
    limit = BEFORE.get(following) if following else None
    if limit is not None:
        tags = tuple(tag for tag in tags if tag in limit)
    return tags


def initial_phrases(titles: Sequence[str], slotted, extracted) -> set[str]:
    """Nouns the corpus is willing to open a title with, article-less.

    Some singular nouns do this comfortably - BALANCE OF TERROR, ERRAND OF
    MERCY, JOURNEY TO BABEL - and some do not: ULTIMATE COMPUTER ON THE WINK
    reads as a missing word, because that phrase never appears without its
    article. Tags cannot tell the two apart; position in the corpus can.
    """
    opening: set[str] = set()
    for title in titles:
        frame = list(slotted(title))
        if frame and frame[0] == SLOT:
            found = extracted(title)
            if found:
                opening.add(found[0])
    return opening


def slots_of(frame: Sequence[str]) -> list[tuple[str | None, str | None]]:
    """Each slot's neighbours: the token before it and the token after it."""
    return [
        (
            frame[index - 1] if index else None,
            frame[index + 1] if index + 1 < len(frame) else None,
        )
        for index, token in enumerate(frame)
        if token == SLOT
    ]


def is_fillable(frame: Sequence[str], lexicon: Sequence[Entity]) -> bool:
    """Can every slot in this frame be filled at all?"""
    available = {entity.tag for entity in lexicon}
    return all(
        set(allowed_tags(before, after)) & available
        for before, after in slots_of(frame)
    )


def render(frame: Sequence[str], choices: Sequence[Entity]) -> str:
    """Assemble the title, fixing A/AN to the word that actually follows."""
    words: list[str] = []
    filled = iter(choices)
    for token in frame:
        if token == SLOT:
            words.append(next(filled).text)
        else:
            words.append(token)
    for index, word in enumerate(words[:-1]):
        if word in ("A", "AN"):
            words[index] = "AN" if words[index + 1][0] in VOWELS else "A"
    return " ".join(words)


def transition_mask(
    frames: Sequence[Sequence[str]], vocabulary: Sequence[str]
) -> list[set[int]]:
    """Which frame tokens may follow which, as observed in the corpus.

    Unconstrained, the model invents adjacencies that never occur and cannot
    be read: "TRISKELION THE MAN TRAP" came from a slot followed by a bare
    determiner, "THE GALILEO SEVEN A RETURN" from the same fault. Both are
    plausible to a model that has only learned token statistics over 241
    examples, and neither is English.

    Restricting each step to a transition the corpus actually contains fixes
    that without pinning the model to whole memorized frames: novel frames are
    still reachable, as new paths through observed steps. On the 6809 this is a
    bitmask per token - twenty tokens, sixty bytes.
    """
    index_of = {token: index for index, token in enumerate(vocabulary)}
    allowed: list[set[int]] = [set() for _ in vocabulary]
    boundary = index_of[BOUNDARY]
    for frame in frames:
        previous = boundary
        for token in frame:
            allowed[previous].add(index_of[token])
            previous = index_of[token]
        allowed[previous].add(boundary)
    return allowed


def title_hash(title: str) -> int:
    """A 16-bit fingerprint, so the CoCo can refuse to emit a real episode.

    Short frames like `<X>` and `THE <X>` produce a real title often - seven
    of sixteen on the first screen - which is a poor showing for a generator
    advertised as making them up. Carrying all 79 titles to compare against
    costs 2.4 KB; carrying two bytes each costs 158, and a false rejection
    only discards a title that was fine, which nobody can see.
    """
    value = 0
    for character in title:
        value = (value * 31 + ord(character)) & 0xFFFF
    return value


def solo_phrases(
    titles: Sequence[str], slotted, extracted
) -> dict[str | None, set[str]]:
    """Nouns the corpus builds a whole title out of, keyed by what precedes them.

    This is evidence, not machinery: it is why one-slot frames are refused.
    Not every noun can carry a title - "The Corbomite Maneuver" is one, "The
    Mark" is not, because MARK only reached the lexicon by having "of Gideon"
    cut off it - and the ones that can are exactly the ones that already do.
    All 39 of them reconstruct their own episode, so a one-slot frame cannot
    produce a novel title. tests/test_title_generator.py holds that check.
    """
    solo: dict[str | None, set[str]] = {}
    for title in titles:
        frame = list(slotted(title))
        if frame.count(SLOT) != 1:
            continue
        index = frame.index(SLOT)
        preceding = frame[index - 1] if index else None
        for phrase in extracted(title):
            solo.setdefault(preceding, set()).add(phrase)
    return solo


class SlotFiller:
    """Draws entities for a frame's slots, without repeating within a title."""

    def __init__(self, lexicon: Sequence[Entity], opening: set[str] | None = None):
        # Kept in lexicon order, not grouped by tag. The CoCo scans the noun
        # table straight through, so a draw index only means the same phrase on
        # both machines if the candidate list is built in the same order.
        self.lexicon = list(lexicon)
        self.opening = opening

    def candidates(self, preceding: str | None, following: str | None) -> list[Entity]:
        admissible = allowed_tags(preceding, following)
        pool = [entity for entity in self.lexicon if entity.tag in admissible]
        if preceding is None and self.opening is not None:
            # A title-initial slot takes any determiner-less noun, plus only
            # those singulars the corpus has actually opened a title with.
            pool = [e for e in pool if e.tag != NS or e.text in self.opening]
        return pool

    def fill(self, frame: Sequence[str], draw) -> list[Entity] | None:
        """`draw(n)` returns an index below n. None if a slot cannot be filled."""
        used: list[Entity] = []
        for preceding, following in slots_of(frame):
            pool = [e for e in self.candidates(preceding, following) if e not in used]
            if not pool:
                return None
            used.append(pool[draw(len(pool))])
        return used


def generate_frame(model, allowed: list[set[int]], random, *, limit: int) -> list[str]:
    """Sample a frame, one token at a time, from the observed transitions only.

    The model supplies byte probabilities exactly as the CoCo will; this
    zeroes the illegal ones and redistributes nothing, drawing against the
    surviving total instead. That keeps the arithmetic to a compare and an add.
    """
    import numpy as np

    boundary = model.token_by_text[BOUNDARY]
    context = [boundary] * model.config.context
    frame: list[str] = []

    for _ in range(limit):
        _, probabilities = model._forward(np.asarray(context, dtype=np.int64))
        legal = allowed[context[-1]]
        weights = [
            int(probability) if token in legal else 0
            for token, probability in enumerate(probabilities)
        ]
        total = sum(weights)
        if total == 0:
            break
        draw = draw_below(random, total)
        running = 0
        chosen = boundary
        for token, weight in enumerate(weights):
            running += weight
            if draw < running:
                chosen = token
                break
        if chosen == boundary:
            break
        frame.append(model.vocabulary[chosen])
        context = context[1:] + [chosen]

    return frame
