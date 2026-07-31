"""Generate printable dice cards from the trained reference model.

Each card is one context — the two tokens the model can currently see — and
lists every next token a visitor can reach by rolling one die. The probabilities
come from `FixedTokenLanguageModel`, so the paper deck samples the same
distribution the CoCo holds in RAM.

Two behaviours are copied deliberately from `generate()` so the deck cannot
drift from the machine:

* Boundary suppression. EXP-004 refuses to end a name before two tokens. That
  rule depends on how many tokens have been emitted, but for a two-token context
  the two are equivalent: a context containing `<END>` is always shorter than two
  tokens in, so suppression is decidable per card.
* Redistribution. The suppressed boundary share moves to the leading token,
  exactly as the CoCo does it.

Rounding to whole die faces is the one place the paper cannot be exact. The
largest-remainder method keeps the deck as close as the die allows, and the
residual is reported so the loss is known rather than hidden.
"""

from __future__ import annotations

import argparse
import html
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from fixed_token_lm import FixedTokenLanguageModel
from token_lm import (
    BOUNDARY,
    ModelConfig,
    build_vocabulary,
    load_names,
    make_examples,
)

SCREEN_BOUNDARY = "#"
PROBABILITY_UNIT = 256


@dataclass(frozen=True)
class Row:
    token: str
    faces: int
    first: int
    last: int
    exact_percent: float
    printed_percent: float

    @property
    def range_text(self) -> str:
        if self.first == self.last:
            return f"{self.first}"
        return f"{self.first}-{self.last}"


@dataclass(frozen=True)
class Card:
    context: tuple[str, str]
    rows: tuple[Row, ...]
    suppressed_boundary: bool
    dropped_tokens: int
    dropped_percent: float

    @property
    def title(self) -> str:
        return "  ".join(display(token) for token in self.context)

    @property
    def carry(self) -> str:
        return display(self.context[1])


def display(token: str) -> str:
    return SCREEN_BOUNDARY if token == BOUNDARY else token


def footer_parts(card: Card) -> tuple[str | None, str | None]:
    """The two things a visitor might need next: an ending, and a lookup."""
    ends = any(row.token == BOUNDARY for row in card.rows)
    continues = any(row.token != BOUNDARY for row in card.rows)
    ending = f"Roll {SCREEN_BOUNDARY} and the name is finished." if ends else None
    lookup = f"{card.carry} + the word you just wrote" if continues else None
    return ending, lookup


def allocate_faces(probabilities: list[int], faces: int) -> list[int]:
    """Largest-remainder allocation of die faces to probability shares."""
    scaled = [probability * faces for probability in probabilities]
    floors = [value // PROBABILITY_UNIT for value in scaled]
    remaining = faces - sum(floors)
    order = sorted(
        range(len(scaled)),
        key=lambda index: (-(scaled[index] % PROBABILITY_UNIT), index),
    )
    for index in order[:remaining]:
        floors[index] += 1
    return floors


def build_card(
    model: FixedTokenLanguageModel,
    context: tuple[int, int],
    *,
    faces: int,
    boundary: int,
) -> Card:
    _, probabilities = model._forward(np.asarray(context, dtype=np.int64))
    probabilities = probabilities.copy()

    suppressed = boundary in context
    if suppressed:
        removed = int(probabilities[boundary])
        probabilities[boundary] = 0
        probabilities[int(np.argmax(probabilities))] += removed

    shares = [int(value) for value in probabilities]
    allocation = allocate_faces(shares, faces)

    rows: list[Row] = []
    cursor = 1
    ranked = sorted(
        range(len(allocation)),
        key=lambda index: (-allocation[index], -shares[index], index),
    )
    for index in ranked:
        if allocation[index] == 0:
            continue
        width = allocation[index]
        rows.append(
            Row(
                token=model.vocabulary[index],
                faces=width,
                first=cursor,
                last=cursor + width - 1,
                exact_percent=shares[index] * 100.0 / PROBABILITY_UNIT,
                printed_percent=width * 100.0 / faces,
            )
        )
        cursor += width

    dropped = [
        shares[index]
        for index in range(len(shares))
        if allocation[index] == 0 and shares[index] > 0
    ]
    return Card(
        context=(model.vocabulary[context[0]], model.vocabulary[context[1]]),
        rows=tuple(rows),
        suppressed_boundary=suppressed,
        dropped_tokens=len(dropped),
        dropped_percent=sum(dropped) * 100.0 / PROBABILITY_UNIT,
    )


def build_deck(
    model: FixedTokenLanguageModel,
    *,
    faces: int,
    max_tokens: int,
    min_path: float,
) -> list[Card]:
    """Every context a visitor is realistically going to reach.

    Reachability is the probability of the most likely walk that arrives at a
    context. Below `min_path` a card would be printed for a route almost nobody
    takes, so the deck stops there and the "off the map" card covers the rest —
    which is a better exhibit anyway than a drawer of cards nobody draws.
    """
    boundary = model.token_by_text[BOUNDARY]
    start = (boundary, boundary)
    best = {start: 1.0}
    queue: deque[tuple[tuple[int, int], int]] = deque([(start, 0)])
    cards: dict[tuple[int, int], Card] = {}

    while queue:
        context, depth = queue.popleft()
        card = build_card(model, context, faces=faces, boundary=boundary)
        cards[context] = card
        if depth >= max_tokens:
            continue
        for row in card.rows:
            token = model.token_by_text[row.token]
            if token == boundary:
                continue
            successor = (context[1], token)
            path = best[context] * row.faces / faces
            if path < min_path or path <= best.get(successor, 0.0):
                continue
            best[successor] = path
            queue.append((successor, depth + 1))

    ordered = sorted(cards, key=lambda context: (-best.get(context, 0.0), context))
    return [cards[context] for context in ordered]


def render_text(cards: list[Card], faces: int) -> str:
    width = 46
    blocks: list[str] = []
    for card in cards:
        lines = ["┌" + "─" * width + "┐"]
        lines.append("│ " + card.title.ljust(width - 2) + " │")
        lines.append("├" + "─" * width + "┤")
        lines.append("│ " + f"Roll 1d{faces}:".ljust(width - 2) + " │")
        lines.append("│" + " " * width + "│")
        for row in card.rows:
            text = (
                f"  {row.range_text:>7}   {display(row.token):<18}"
                f"{row.printed_percent:5.0f}%"
            )
            lines.append("│ " + text.ljust(width - 2) + " │")
        lines.append("│" + " " * width + "│")
        lines.append("├" + "─" * width + "┤")
        ending, lookup = footer_parts(card)
        for footer in (ending, f"Next card:  {lookup}" if lookup else None):
            if footer:
                lines.append("│ " + footer.ljust(width - 2) + " │")
        lines.append("└" + "─" * width + "┘")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def stylesheet(accent: str) -> str:
    """Print-first: black on white, colour only in the deck band."""
    return f"""
@page {{ size: letter; margin: 0.4in; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; color: #111; background: #fff;
       font-family: "Helvetica Neue", Arial, sans-serif; }}
.sheet {{ display: grid; grid-template-columns: 1fr 1fr;
         grid-template-rows: 1fr 1fr; gap: 0.2in;
         height: 10.2in; page-break-after: always; }}
.card {{ border: 2px solid #111; border-radius: 6px; padding: 0.22in;
        display: flex; flex-direction: column; overflow: hidden; }}
.band {{ height: 0.16in; background: {accent}; border-radius: 3px 3px 0 0;
        margin: -0.22in -0.22in 0.14in -0.22in; }}
.deck {{ font-size: 7.5pt; text-transform: uppercase; color: #777;
        letter-spacing: 0.14em; }}
.ctx {{ font-size: 27pt; font-weight: 800; letter-spacing: 0.01em;
       line-height: 1.05; margin: 0.02in 0 0.02in; }}
.prompt {{ font-size: 9.5pt; color: #555; margin: 0 0 0.1in; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13.5pt; }}
td {{ padding: 2.5pt 0; border-bottom: 1px solid #e8e8e8; }}
.range {{ width: 24%; font-weight: 700; font-variant-numeric: tabular-nums; }}
.word {{ font-weight: 600; }}
.pct {{ width: 20%; text-align: right; color: #777;
       font-variant-numeric: tabular-nums; }}
.foot {{ margin-top: auto; padding-top: 0.1in; border-top: 2px solid #111;
        font-size: 9.5pt; line-height: 1.5; }}
.next b {{ font-size: 12pt; }}
""".strip()


def render_html(cards: list[Card], faces: int, label: str, accent: str) -> str:
    parts = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        f"<title>{html.escape(label)} deck</title>",
        f"<style>{stylesheet(accent)}</style></head><body>",
    ]

    for offset in range(0, len(cards), 4):
        parts.append('<div class="sheet">')
        for card in cards[offset : offset + 4]:
            parts.append('<div class="card">')
            parts.append('<div class="band"></div>')
            parts.append(f'<div class="deck">{html.escape(label)}</div>')
            parts.append(f'<p class="ctx">{html.escape(card.title)}</p>')
            parts.append(
                f'<p class="prompt">Roll 1d{faces} and write the word down.</p>'
            )
            parts.append("<table>")
            for row in card.rows:
                parts.append(
                    "<tr>"
                    f'<td class="range">{row.range_text}</td>'
                    f'<td class="word">{html.escape(display(row.token))}</td>'
                    f'<td class="pct">{row.printed_percent:.0f}%</td>'
                    "</tr>"
                )
            parts.append("</table>")
            ending, lookup = footer_parts(card)
            parts.append('<div class="foot">')
            if ending:
                parts.append(f"<div>{html.escape(ending)}</div>")
            if lookup:
                carry = html.escape(card.carry)
                rest = html.escape(lookup.split(" + ", 1)[1])
                parts.append(
                    f'<div class="next">Next card: <b>{carry}</b> + {rest}</div>'
                )
            parts.append("</div>")
            parts.append("</div>")
        parts.append("</div>")

    parts.append("</body></html>")
    return "\n".join(parts)


def parse_arguments() -> argparse.Namespace:
    default_corpus = (
        ROOT / "experiments" / "data" / "EXP-002-tokenized-computer-names.txt"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=default_corpus)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--seed", type=int, default=6809)
    parser.add_argument("--faces", type=int, default=20, help="die faces (20 or 100)")
    parser.add_argument("--max-tokens", type=int, default=6)
    parser.add_argument(
        "--min-path",
        type=float,
        default=0.01,
        help="drop contexts reached by fewer than this share of walks",
    )
    parser.add_argument("--format", choices=("text", "html"), default="text")
    parser.add_argument("--label", default="COCO-LLM", help="deck name on each card")
    parser.add_argument("--accent", default="#111111", help="deck colour band")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    names = load_names(arguments.corpus)
    vocabulary, token_by_text = build_vocabulary(names)
    contexts, targets = make_examples(names, token_by_text, context_size=2)

    model = FixedTokenLanguageModel(ModelConfig(seed=arguments.seed), vocabulary)
    model.train(contexts, targets, epochs=arguments.epochs)

    cards = build_deck(
        model,
        faces=arguments.faces,
        max_tokens=arguments.max_tokens,
        min_path=arguments.min_path,
    )

    if arguments.format == "html":
        rendered = render_html(
            cards, arguments.faces, arguments.label, arguments.accent
        )
    else:
        rendered = render_text(cards, arguments.faces)

    if arguments.output:
        arguments.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)

    worst = max(cards, key=lambda card: card.dropped_percent)
    total_dropped = sum(card.dropped_percent for card in cards) / len(cards)
    print(
        f"\ncards: {len(cards)}"
        f"\ncorpus: {arguments.corpus.name}"
        f"\nchecksum: {model.checksum()[:16]}"
        f"\ndie: d{arguments.faces}"
        f"\nmean probability below one face: {total_dropped:.1f}%"
        f"\nworst card: {worst.title.strip()} at {worst.dropped_percent:.1f}%",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
