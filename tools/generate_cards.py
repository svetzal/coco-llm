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
    """Four landscape cards on a letter sheet, styled like a CoCo manual."""
    return f"""
@page {{ size: letter landscape; margin: 0.25in; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #fff; }}
body {{
  color: #0a160b;
  font-family: Avenir Next, Avenir, Futura, sans-serif;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
@media screen {{
  body {{ background: #d7d5ce; padding: 0.25in; }}
  .sheet {{
    background: #fff;
    box-shadow: 0 0.08in 0.28in rgb(0 0 0 / 18%);
    margin: 0 auto 0.25in;
  }}
}}
.sheet {{
  width: 10.5in;
  height: 8in;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-template-rows: repeat(2, minmax(0, 1fr));
  gap: 0.14in;
  break-after: page;
  page-break-after: always;
}}
.sheet:last-child {{ break-after: auto; page-break-after: auto; }}
.card {{
  --ink: #071508;
  --screen: #25c925;
  --screen-dark: #052706;
  --paper: #f3ecd8;
  background: var(--paper);
  border: 1.8pt solid var(--ink);
  border-radius: 0.08in;
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  overflow: hidden;
  min-width: 0;
}}
.screen {{
  background: var(--screen);
  border-bottom: 1.6pt solid var(--ink);
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-height: 0;
  padding: 0.09in 0.12in 0.07in;
}}
.screen-head {{
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  column-gap: 0.12in;
  border-bottom: 1.5pt solid var(--screen-dark);
  padding-bottom: 0.045in;
  margin-bottom: 0.035in;
}}
.step-label {{
  display: block;
  color: var(--screen-dark);
  font: 800 5.9pt/1 Avenir Next, Avenir, Futura, sans-serif;
  letter-spacing: 0.13em;
  text-transform: uppercase;
  margin-bottom: 0.018in;
}}
.ctx {{
  color: var(--screen-dark);
  font-family: Menlo, Monaco, Courier New, monospace;
  font-size: 29pt;
  font-weight: 700;
  letter-spacing: 0.04em;
  line-height: 0.96;
  margin: 0;
  overflow-wrap: anywhere;
  text-transform: uppercase;
}}
.roll {{
  align-items: center;
  color: var(--screen-dark);
  display: flex;
  font: 900 11pt/1 Avenir Next, Avenir, Futura, sans-serif;
  gap: 0.055in;
  padding-bottom: 0.012in;
  white-space: nowrap;
}}
.roll-label {{ display: grid; gap: 0.015in; }}
.roll-label .step-label {{ margin: 0; }}
.die {{ height: 0.38in; width: 0.38in; flex: none; }}
.die text {{ font: 900 8px/1 Menlo, Monaco, monospace; }}
.distribution {{
  align-self: stretch;
  border-collapse: collapse;
  color: var(--screen-dark);
  font-family: Menlo, Monaco, Courier New, monospace;
  font-size: 9.1pt;
  font-weight: 700;
  line-height: 1;
  table-layout: fixed;
  width: 100%;
}}
.distribution td {{ padding: 1.25pt 0; }}
.distribution .range {{ width: 24%; font-variant-numeric: tabular-nums; }}
.distribution .word {{ width: 56%; }}
.distribution .pct {{ width: 20%; text-align: right;
                      font-variant-numeric: tabular-nums; }}
.distribution.dense {{ font-size: 7.3pt; }}
.distribution.dense td {{ padding: 0.55pt 0; }}
.manual {{
  background: var(--paper);
  display: grid;
  grid-template-rows: auto auto;
}}
.instruction {{
  align-items: center;
  display: flex;
  font-size: 7.2pt;
  gap: 0.08in;
  line-height: 1.15;
  min-height: 0.46in;
  padding: 0.055in 0.12in;
}}
.instruction-copy {{ flex: 1 1 auto; min-width: 0; }}
.step-badge {{
  align-items: center;
  background: var(--ink);
  border-radius: 0.035in;
  color: var(--paper);
  display: flex;
  font-size: 12pt;
  font-weight: 900;
  height: 0.27in;
  justify-content: center;
  flex: none;
  width: 0.27in;
}}
.instruction-title {{
  display: block;
  font-size: 7pt;
  font-weight: 900;
  letter-spacing: 0.08em;
  margin-bottom: 0.02in;
  text-transform: uppercase;
}}
.next-context {{ font-size: 8.5pt; }}
.next-context b {{ font-size: 10.5pt; }}
.ending {{
  border: 1.2pt solid var(--ink);
  font-size: 6.6pt;
  font-weight: 800;
  padding: 0.04in 0.055in;
  flex: none;
  text-transform: uppercase;
  white-space: nowrap;
}}
.brand {{
  align-items: center;
  background: var(--ink);
  color: var(--paper);
  display: grid;
  gap: 0.08in;
  grid-template-columns: auto 1fr auto;
  min-height: 0.24in;
  padding: 0.035in 0.12in;
}}
.spectrum {{ display: flex; gap: 0.018in; }}
.spectrum i {{ display: block; height: 0.075in; transform: skewX(-24deg);
               width: 0.19in; }}
.spectrum i:nth-child(1) {{ background: #d73521; }}
.spectrum i:nth-child(2) {{ background: #ee791d; }}
.spectrum i:nth-child(3) {{ background: #e3bb22; }}
.spectrum i:nth-child(4) {{ background: #4a8e3a; }}
.spectrum i:nth-child(5) {{ background: #2c5f9f; }}
.brand-name {{
  font-size: 7.1pt;
  font-weight: 900;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}}
.deck {{
  border-left: 0.055in solid {accent};
  font-size: 5.8pt;
  letter-spacing: 0.12em;
  padding-left: 0.06in;
  text-transform: uppercase;
  white-space: nowrap;
}}
""".strip()


def render_d20() -> str:
    """A small line-art die that stays crisp in print."""
    return """
<svg class="die" viewBox="0 0 48 48" aria-hidden="true">
  <g fill="none" stroke="#052706" stroke-linecap="round"
     stroke-linejoin="round" stroke-width="1.5">
    <polygon points="24,2 43,14 39,37 24,46 9,37 5,14" />
    <path d="M24 2 15 17 5 14m19-12 9 15 10-3M15 17l9 12 9-12M9 37l15-8 15 8M9 37l15 9 15-9" />
  </g>
  <circle cx="24" cy="25" r="6" fill="#25c925" />
  <text x="24" y="28" fill="#052706" text-anchor="middle">20</text>
</svg>
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
            parts.append('<section class="screen">')
            parts.append('<header class="screen-head">')
            parts.append("<div>")
            parts.append('<span class="step-label">1 · Current context</span>')
            parts.append(f'<p class="ctx">{html.escape(card.title)}</p>')
            parts.append("</div>")
            parts.append('<div class="roll">')
            parts.append('<span class="roll-label">')
            parts.append('<span class="step-label">2 · Roll</span>')
            parts.append(f"<span>1d{faces}</span>")
            parts.append("</span>")
            parts.append(render_d20())
            parts.append("</div>")
            parts.append("</header>")
            density = " dense" if len(card.rows) > 9 else ""
            parts.append(f'<table class="distribution{density}">')
            for row in card.rows:
                parts.append(
                    "<tr>"
                    f'<td class="range">{row.range_text}</td>'
                    f'<td class="word">{html.escape(display(row.token))}</td>'
                    f'<td class="pct">{row.printed_percent:.0f}%</td>'
                    "</tr>"
                )
            parts.append("</table>")
            parts.append("</section>")
            ending, lookup = footer_parts(card)
            parts.append('<footer class="manual">')
            parts.append('<div class="instruction">')
            parts.append('<span class="step-badge">3</span>')
            parts.append('<div class="instruction-copy">')
            parts.append('<span class="instruction-title">Find next card</span>')
            if lookup:
                carry = html.escape(card.carry)
                rest = html.escape(lookup.split(" + ", 1)[1])
                parts.append(f'<div class="next-context"><b>{carry}</b> + {rest}</div>')
            else:
                parts.append('<div class="next-context">No next card</div>')
            parts.append("</div>")
            if ending:
                parts.append(f'<div class="ending">{html.escape(ending)}</div>')
            parts.append("</div>")
            parts.append('<div class="brand">')
            parts.append(
                '<span class="spectrum" aria-hidden="true">'
                "<i></i><i></i><i></i><i></i><i></i></span>"
            )
            parts.append('<span class="brand-name">CoCo LLM · Be the model</span>')
            parts.append(f'<span class="deck">{html.escape(label)}</span>')
            parts.append("</div>")
            parts.append("</footer>")
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
