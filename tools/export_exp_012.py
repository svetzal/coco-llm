#!/usr/bin/env python3
"""Train the EXP-012 title model on the Mac and emit it for the CoCo.

The Mac does the learning; the CoCo does the generating. Everything the 6809
needs is written here as assembly data, and it all comes from the same
`build()` the reference driver uses, so there is one trained model rather than
two that have to be kept in step.

Six tables cross over:

  parameters   Q4.12 masters, copied into RAM at startup so the shared forward
               pass in model_core.asm runs against them unmodified.
  frame words  the closed-class vocabulary, as printable strings.
  transitions  a bit per legal successor. This is what keeps the decoder from
               inventing adjacencies the corpus never states.
  nouns        the phrases, with a tag byte carrying the grammatical class and
               whether the phrase may open a title without an article.
  tag rules    the admissible classes either side of a slot, one byte each.
  fingerprints two bytes per real episode, so the CoCo can decline to emit one.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))
sys.path.insert(0, str(ROOT / "tools"))

from run_exp_012 import build
from run_exp_012 import parse_arguments as reference_arguments
from title_generator import (
    AFTER_DETERMINER,
    BARE,
    BEFORE,
    NM,
    NPL,
    NS,
    PN,
    SLOT,
    TAGS,
    initial_phrases,
    title_hash,
)
from token_lm import BOUNDARY

DEFAULT_OUTPUT = ROOT / "build" / "exp012" / "title_model.inc"
BIT = {NS: 0x01, NM: 0x02, NPL: 0x04, PN: 0x08}
OPENS = 0x10  # may begin a title with no article in front of it
ALL_TAGS = 0x0F


def worst_logit(model) -> int:
    """The largest logit any reachable context can produce, before rounding.

    Every context is two tokens, so there are only VOCAB^2 of them and the
    bound can be measured rather than estimated.
    """
    import numpy as np

    size = model.vocabulary_size
    embedding = model.config.embedding
    peak = 0
    for first in range(size):
        for second in range(size):
            vector = np.zeros(embedding, dtype=np.int64)
            for position, token in enumerate((first, second)):
                vector += model.position_embeddings[position, token] >> 8
            for output in range(size):
                total = (model.output_biases[output] >> 8) << 4
                for dimension in range(embedding):
                    weight = model.output_weights[output, dimension] >> 8
                    total += int(weight) * int(vector[dimension])
                peak = max(peak, abs(int(total)))
    return peak


def mask_of(tags) -> int:
    return sum(BIT[tag] for tag in tags)


def label_of(text: str, index: int) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in text) or "boundary"
    return f"t12_{index:03d}_{safe}"[:40]


def bytes_block(name: str, values, width: int = 16) -> list[str]:
    lines = [name]
    for offset in range(0, len(values), width):
        chunk = values[offset : offset + width]
        lines.append("        fcb     " + ",".join(f"${v & 0xFF:02x}" for v in chunk))
    return lines


def words_block(values, width: int = 8) -> list[str]:
    return [
        "        fdb     "
        + ",".join(f"${v & 0xFFFF:04x}" for v in values[o : o + width])
        for o in range(0, len(values), width)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    known, rest = parser.parse_known_args()
    sys.argv = [sys.argv[0], *rest]
    arguments = reference_arguments()

    model, _, allowed, lexicon, titles, facts = build(arguments)
    vocabulary = model.vocabulary
    index_of = model.token_by_text
    opening = initial_phrases(titles, *facts["slotting"])

    # model_forward.asm accumulates a logit in D and stores it, so it wraps at
    # 16 bits where the reference clamps. Every experiment before this one kept
    # activations small enough that the difference never showed; this model's
    # do not, unless training stops early. Refuse to ship a model that would
    # make the CoCo and the Mac disagree.
    peak = worst_logit(model)
    if peak > 32767:
        raise SystemExit(
            f"peak |logit| {peak} leaves int16: the CoCo would wrap where the "
            f"reference clamps. Train for fewer epochs."
        )

    lines: list[str] = [
        "; Generated EXP-012 title model. Do not edit.",
        f"; peak |logit| {peak} of 32767",
        (
            f"; {len(facts['frames'])} frames, {len(lexicon)} noun phrases, "
            f"loss {facts['losses'][-1]:.4f}"
        ),
        "",
        f"VOCAB_SIZE      equ     {len(vocabulary)}",
        f"SLOT_TOKEN      equ     {index_of[SLOT]}",
        f"NOUN_COUNT      equ     {len(lexicon)}",
        f"REAL_COUNT      equ     {len(titles)}",
        f"TAG_ALL         equ     ${ALL_TAGS:02x}",
        f"TAG_OPENS       equ     ${OPENS:02x}",
        f"TAG_NS          equ     ${BIT[NS]:02x}",
        f"ARTICLE_A       equ     {index_of.get('A', 0xFF)}",
        f"ARTICLE_AN      equ     {index_of.get('AN', 0xFF)}",
        "MAX_FRAME       equ     8",
        "",
    ]

    # Parameters, in the order model_storage.asm lays them out.
    flat: list[int] = []
    for position in range(model.config.context):
        for token in range(model.vocabulary_size):
            flat += [int(v) for v in model.position_embeddings[position, token]]
    for token in range(model.vocabulary_size):
        flat += [int(v) for v in model.output_weights[token]]
    flat += [int(v) for v in model.output_biases]
    lines.append("title_parameters")
    lines += words_block(flat)
    lines.append(f"TITLE_PARAM_BYTES equ  {2 * len(flat)}")
    lines.append("")

    # Frame words. The boundary and the slot never print.
    lines.append("frame_word_table")
    lines += words_block([0] * 0)
    for index, token in enumerate(vocabulary):
        lines.append(f"        fdb     {label_of(token, index)}")
    lines.append("")
    for index, token in enumerate(vocabulary):
        text = "" if token in (BOUNDARY, SLOT) else token
        body = ",".join(f"${ord(c):02x}" for c in text)
        lines.append(f"{label_of(token, index)} fcb     {body + ',' if body else ''}0")
    lines.append("")

    # Legal successors, three bytes per token, high bit first.
    successors: list[int] = []
    for token in range(len(vocabulary)):
        bits = 0
        for following in allowed[token]:
            bits |= 1 << following
        successors += [bits & 0xFF, (bits >> 8) & 0xFF, (bits >> 16) & 0xFF]
    lines += bytes_block("frame_successors", successors, width=12)
    lines.append("")

    # What may fill a slot, by the token before it and the token after it.
    after = [mask_of(AFTER_DETERMINER.get(token, BARE)) for token in vocabulary]
    before = [mask_of(BEFORE.get(token, TAGS)) for token in vocabulary]
    lines += bytes_block("slot_tags_after", after)
    lines.append("")
    lines += bytes_block("slot_tags_before", before)
    lines.append("")

    # Nouns: pointer, then a tag byte carrying class and opening permission.
    lines.append("noun_table")
    for index in range(len(lexicon)):
        lines.append(f"        fdb     n12_{index:03d}")
    lines.append("")
    tags = [
        BIT[entity.tag] | (OPENS if entity.text in opening else 0) for entity in lexicon
    ]
    lines += bytes_block("noun_tags", tags)
    lines.append("")
    for index, entity in enumerate(lexicon):
        body = ",".join(f"${ord(c):02x}" for c in entity.text)
        lines.append(f"n12_{index:03d} fcb     {body},0")
    lines.append("")

    # softmax in model_core.asm reads this table; it is the same curve the
    # reference uses, so the two agree byte for byte.
    from fixed_token_lm import EXP_LUT

    lines += bytes_block("exp_lut", [int(v) for v in EXP_LUT])
    lines.append("")

    lines += bytes_block(
        "real_titles",
        [b for title in titles for b in title_hash(title).to_bytes(2, "big")],
    )
    lines.append("")

    known.output.parent.mkdir(parents=True, exist_ok=True)
    known.output.write_text("\n".join(lines) + "\n", encoding="ascii")

    parameters = 2 * len(flat)
    frame_text = sum(len(t) + 1 for t in vocabulary if t not in (BOUNDARY, SLOT))
    nouns = sum(len(e.text) + 1 for e in lexicon)
    total = (
        parameters
        + 2 * len(vocabulary)
        + frame_text
        + len(successors)
        + 2 * len(vocabulary)
        + 2 * len(lexicon)
        + len(tags)
        + nouns
        + 2 * len(titles)
    )
    print(f"wrote {known.output}")
    print(f"  parameters (Q4.12)   {parameters:>6}")
    print(f"  frame words          {2 * len(vocabulary) + frame_text:>6}")
    print(f"  transition bitmasks  {len(successors):>6}")
    print(f"  slot tag rules       {2 * len(vocabulary):>6}")
    print(f"  noun table           {2 * len(lexicon) + len(tags) + nouns:>6}")
    print(f"  real-title hashes    {2 * len(titles):>6}")
    print(f"  data total           {total:>6} bytes")


if __name__ == "__main__":
    main()
