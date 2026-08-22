#!/usr/bin/env python3
"""Build the deck's figures from the exported traces and splice them in.

The deck is hand-edited, so this does not generate index.html. It replaces the
contents of marked regions:

    <!-- FIGURE:name -->  ...generated...  <!-- /FIGURE:name -->

Everything outside those markers is yours. Everything inside is derived from
data/traces.json and will be overwritten, which is the point: a figure that can
drift away from the model is a figure that will eventually lie on stage.

Animation is reveal fragments only. Where a figure shows a before and an after,
the after is drawn on top as a fragment, so stepping backwards undoes it.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
DECK = ROOT / "presentation" / "deck" / "index.html"
TRACES = ROOT / "presentation" / "deck" / "data" / "traces.json"


def esc(text: str) -> str:
    return html.escape(str(text))


def figure_vocabulary(trace: dict) -> str:
    """What the machine thinks a word is, and where examples come from."""
    vocabulary = trace["vocabulary"]
    hot = {t["id"] for t in trace["focus_tokens"]}

    cells = "".join(
        f'<div class="tok{" hot" if i in hot else ""}">'
        f'<span class="id">{i}</span>{esc(t)}</div>'
        for i, t in enumerate(vocabulary)
    )

    rows = []
    for n, w in enumerate(trace["walk"]):
        ctx = "".join(
            f'<span class="cell ctx">{esc(t)}</span>' for t in w["context_text"]
        )
        rows.append(
            f'<div class="win-row fragment" data-fragment-index="{n + 2}">'
            f'{ctx}<span class="arrow">&rarr;</span>'
            f'<span class="cell tgt">{esc(w["target_text"])}</span></div>'
        )

    return f"""
  <p class="lbl">{len(vocabulary)} tokens. A person chose every one.</p>
  <div class="fig">
    <div class="vocab">{cells}</div>
    <p class="fragment lbl" data-fragment-index="1">
      {esc(trace["focus"])} is
      {" and ".join(str(t["id"]) for t in trace["focus_tokens"])}
    </p>
    <div class="slide-window">{"".join(rows)}</div>
    <p class="lbl">{trace["names"]} names become {trace["examples"]} examples</p>
  </div>"""


def figure_tables(trace: dict) -> str:
    """The lookup table itself, so a fetched row has somewhere to come from."""
    columns = []
    for table in trace["tables"]:
        rows = "".join(
            f'<div class="trow{" used" if r["used"] else ""}">'
            f'<span class="w">{esc(r["text"])}</span>'
            + "".join(f'<span class="v">{v:+.4f}</span>' for v in r["row"])
            + "</div>"
            for r in table["rows"]
        )
        columns.append(
            f'<div class="tcol">'
            f'<p class="lbl">slot {table["slot"]}</p>'
            f'<div class="tbl">{rows}</div></div>'
        )

    pull = "".join(
        f'<div class="look"><span class="slot">slot {l["slot"]}</span>'
        f'<span class="who">{esc(l["text"])}</span><span class="vec">'
        + "".join(f'<span class="num">{v:+.4f}</span>' for v in l["row"])
        + "</span></div>"
        for l in trace["lookups"]
    )
    total = "".join(
        f'<span class="num moved">{v:+.4f}</span>'
        for v in trace["vector_display"]
    )

    return f"""
  <div class="fig tables">
    <div class="tcols">{"".join(columns)}</div>
    <div class="pull fragment" data-fragment-index="1">
      {pull}
      <div class="look sum">
        <span class="slot"></span><span class="who">add them</span>
        <span class="vec">{total}</span>
      </div>
    </div>
    <p class="cap">two slots, 29 words, three numbers each.
      <strong>174 of the model's 290 numbers are this table.</strong></p>
  </div>"""


def figure_step(trace: dict, vocabulary: list[str]) -> str:
    """One training step, with the numbers that actually moved."""
    before = trace["probabilities_before"]
    after = trace["probabilities_after"]
    target = trace["target"]
    top = max(max(before), max(after))

    bars = []
    for i, p in enumerate(before):
        height = 100 * p / top
        classes = "bar target" if i == target else "bar"
        overlay = ""
        if i == target:
            overlay = (
                f'<span class="after fragment" data-fragment-index="7" '
                f'style="height:{100 * after[i] / top:.1f}%"></span>'
                f'<span class="barlab">{esc(vocabulary[i])}</span>'
            )
        bars.append(
            f'<div class="{classes}" style="height:{height:.1f}%">{overlay}</div>'
        )

    def numbers(values, index=None, moved=False):
        cls = " moved" if moved else ""
        frag = (
            f' fragment" data-fragment-index="{index}'
            if index is not None
            else ""
        )
        return "".join(
            f'<span class="num{cls}{frag}">{v:+.4f}</span>' for v in values
        )

    def row(cells, cls=""):
        return "".join(
            f'<span class="num{cls}">{v:+.4f}</span>' for v in cells
        )

    lookups = "".join(
        f'<div class="look fragment" data-fragment-index="{n + 1}">'
        f'<span class="slot">slot {l["slot"]}</span>'
        f'<span class="who">{esc(l["text"])}</span>'
        f'<span class="vec">{row(l["row"])}</span></div>'
        for n, l in enumerate(trace["lookups"])
    )

    return f"""
  <div class="fig step">
    <p class="half">predict</p>
    <div class="step-row">
      <div class="stage">
        <p class="lbl">every slot and word owns a stored row</p>
        <div class="lookup">
          {lookups}
          <div class="look sum fragment" data-fragment-index="3">
            <span class="slot"></span>
            <span class="who">add them</span>
            <span class="vec">{row(trace["vector_display"], " moved")}</span>
          </div>
        </div>
      </div>
      <div class="stage fragment" data-fragment-index="4">
        <p class="lbl">a score for every token</p>
        <div class="bars">{"".join(bars)}</div>
      </div>
    </div>

    <p class="half fragment" data-fragment-index="5">correct</p>
    <div class="step-row">
      <div class="stage fragment" data-fragment-index="5">
        <p class="lbl">right answer</p>
        <div class="vec">
          <span class="num moved">{esc(trace["target_text"])}</span>
        </div>
        <p class="lbl">it gave it {trace["target_p_before"] * 100:.1f}%</p>
      </div>
      <div class="stage fragment" data-fragment-index="6">
        <p class="lbl">its weights</p>
        <div class="vec">{numbers(trace["target_weights_before"])}</div>
      </div>
      <div class="stage fragment" data-fragment-index="7">
        <p class="lbl">nudged</p>
        <div class="vec">
          {"".join(f'<span class="num moved">{v:+.4f}</span>'
                   for v in trace["target_weights_after"])}
        </div>
        <p class="lbl">now {trace["target_p_after"] * 100:.1f}%</p>
      </div>
    </div>
  </div>"""


def figure_why_three(trace: dict) -> str:
    """Why the embedding is three numbers wide. It was a choice, not a limit."""
    rows = "".join(
        f'<div class="wrow{" chosen" if r["chosen"] else ""}">'
        f'<span class="c n">{r["embedding"]}</span>'
        f'<span class="c">{r["parameters"]}</span>'
        f'<span class="c">{r["total"]:,}</span>'
        f'<span class="c">{r["floor_seconds"]:.1f}s</span></div>'
        for r in trace["widths"]
    )
    rejected = trace["rejected"]
    return f"""
  <div class="fig why">
    <div class="wtable">
      <div class="wrow head">
        <span class="c n">numbers<br>per word</span>
        <span class="c">parameters</span>
        <span class="c">multiplies<br>to train</span>
        <span class="c">MUL time<br>alone</span>
      </div>
      {rows}
    </div>
    <p class="cap fragment" data-fragment-index="1">
      The model this replaced needed
      <strong>{rejected["multiplies"]:,}</strong> multiplies:
      {rejected["floor_seconds"]:.0f} seconds of bare MUL instructions against a
      {trace["budget_seconds"]}-second budget. It was rejected for it.
    </p>
    <p class="cap fragment" data-fragment-index="2">
      So six would have fit here too.
      <strong>Three is what we tried first, and it worked.</strong>
    </p>
  </div>"""


def figure_loop(trace: dict) -> str:
    """What it makes as the loop runs. Includes where it stops improving."""
    rows = []
    for n, epoch in enumerate(trace["checkpoints"]):
        samples = trace["samples"][str(epoch)]
        late = " late" if epoch >= 20 else ""
        rows.append(
            f'<div class="epoch{late} fragment" data-fragment-index="{n}">'
            f'<span class="n">epoch {epoch}</span>'
            f'<span class="out">{esc(samples[0])}</span></div>'
        )
    first, last = trace["losses"][0], trace["losses"][-1]
    return f"""
  <div class="fig">
    <div class="epochs">{"".join(rows)}</div>
    <p class="lbl">loss {first:.2f} &rarr; {last:.2f} across
      {trace["epochs"]} epochs, {trace["parameter_count"]} parameters</p>
  </div>"""


def splice(source: str, name: str, body: str) -> str:
    pattern = re.compile(
        rf"(<!-- FIGURE:{re.escape(name)} -->).*?(<!-- /FIGURE:{re.escape(name)} -->)",
        re.S,
    )
    if not pattern.search(source):
        raise SystemExit(f"no marker region for figure {name!r} in the deck")
    return pattern.sub(lambda m: f"{m.group(1)}{body}\n  {m.group(2)}", source)


def main() -> None:
    traces = json.loads(TRACES.read_text())
    vocabulary = traces["vocabulary"]["vocabulary"]

    deck = DECK.read_text()
    deck = splice(deck, "vocabulary", figure_vocabulary(traces["vocabulary"]))
    deck = splice(deck, "tables", figure_tables(traces["step"]))
    deck = splice(deck, "step", figure_step(traces["step"], vocabulary))
    deck = splice(deck, "why", figure_why_three(traces["why_three"]))
    deck = splice(deck, "loop", figure_loop(traces["loop"]))
    DECK.write_text(deck, encoding="utf-8")
    print("spliced 5 figures into presentation/deck/index.html")


if __name__ == "__main__":
    main()
