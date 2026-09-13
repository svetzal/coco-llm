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
import subprocess
import sys
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

    context = len(trace["walk"][0]["context_text"])
    return f"""
  <div class="fig">
    <div class="vocab">{cells}</div>
    <p class="fragment lbl" data-fragment-index="1">
      {esc(trace["focus"])} is
      {" and ".join(str(t["id"]) for t in trace["focus_tokens"])}
    </p>
    <div class="slide-window">{"".join(rows)}</div>
    <p class="cap fragment" data-fragment-index="2">
      Those {context} boxes are the <strong>context window</strong>. Here it
      holds {context} tokens. It slides, and everything before it is gone.
    </p>
    <p class="cap">{trace["names"]} names become
      {trace["examples"]} training examples</p>
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
            f'<p class="lbl">window position {table["slot"]}</p>'
            f'<div class="tbl">{rows}</div></div>'
        )

    pull = "".join(
        f'<div class="look"><span class="slot">position {l["slot"]}</span>'
        f'<span class="who">{esc(l["text"])}</span><span class="vec">'
        + "".join(f'<span class="num">{v:+.4f}</span>' for v in l["row"])
        + "</span></div>"
        for l in trace["lookups"]
    )
    total = "".join(
        f'<span class="num moved">{v:+.4f}</span>' for v in trace["vector_display"]
    )

    return f"""
  <div class="fig tables">
    <p class="cap top">A context window of {len(trace["tables"])} tokens means
      <strong>{len(trace["tables"])} tables</strong>, one for each position in
      it.</p>
    <div class="tcols">{"".join(columns)}</div>
    <div class="pull fragment" data-fragment-index="1">
      {pull}
      <div class="look sum">
        <span class="slot"></span><span class="who">add them</span>
        <span class="vec">{total}</span>
      </div>
    </div>
    <p class="cap">Two window positions, 29 tokens, three numbers each.
      <strong>174 of the model's 290 parameters are these two tables.</strong>
      </p>
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
                f'<span class="after fragment" data-fragment-index="6" '
                f'style="height:{100 * after[i] / top:.1f}%"></span>'
                f'<span class="barlab">{esc(vocabulary[i])}</span>'
            )
        bars.append(
            f'<div class="{classes}" style="height:{height:.1f}%">{overlay}</div>'
        )

    def numbers(values, index=None, moved=False):
        cls = " moved" if moved else ""
        frag = f' fragment" data-fragment-index="{index}' if index is not None else ""
        return "".join(f'<span class="num{cls}{frag}">{v:+.4f}</span>' for v in values)

    def row(cells, cls=""):
        return "".join(f'<span class="num{cls}">{v:+.4f}</span>' for v in cells)

    lookups = "".join(
        f'<div class="look fragment" data-fragment-index="{n + 1}">'
        f'<span class="slot">position {l["slot"]}</span>'
        f'<span class="who">{esc(l["text"])}</span>'
        f'<span class="vec">{row(l["row"])}</span></div>'
        for n, l in enumerate(trace["lookups"])
    )

    def band(cls, label, values, arrows=False, index=None):
        frag = f' fragment" data-fragment-index="{index}' if index is not None else ""
        cells = []
        for i, v in enumerate(values):
            arrow = ""
            if arrows:
                up = trace["nudges"][i]["up"]
                cls_i = f"{cls} {'up' if up else 'dn'}"
                arrow = f'<span class="arrow">{"&uarr;" if up else "&darr;"}</span>'
            else:
                cls_i = cls
            cells.append(f'<span class="nv {cls_i}">{arrow}{v:+.4f}</span>')
        return (
            f'<div class="nrow{frag}"><span class="nlab">{label}</span>'
            + "".join(cells)
            + "</div>"
        )

    incoming = [n["incoming"] for n in trace["nudges"]]
    before = [n["before"] for n in trace["nudges"]]
    change = [n["change"] for n in trace["nudges"]]
    after = [n["after"] for n in trace["nudges"]]

    return f"""
  <div class="fig step">
    <p class="half">predict</p>
    <div class="step-row">
      <div class="stage">
        <p class="lbl">one stored row per window position and token</p>
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

    <p class="half fragment" data-fragment-index="3">correct</p>
    <div class="step-row">
      <div class="stage fragment" data-fragment-index="3">
        <p class="lbl">the right answer was
          <span class="hot">{esc(trace["target_text"])}</span>,
          and it gave {esc(trace["target_text"])}
          {trace["target_p_before"] * 100:.1f}%</p>
        <div class="nudge">
          {band("in", "the three numbers", incoming)}
          <div class="owner fragment" data-fragment-index="4">
            <p class="ownerlab">{esc(trace["target_text"])}'s three weights</p>
            {band("was", "before", before)}
            {band("chg", "change", change, arrows=True, index=5)}
            {band("now", "after", after, index=6)}
          </div>
        </div>
        <div class="formula fragment" data-fragment-index="5">
          <div class="frow">
            <span class="fterm">change</span><span class="fop">=</span>
            <span class="fterm hot">{trace["learning_rate"]}</span>
            <span class="fop">&times;</span>
            <span class="fterm hot">{trace["wrongness"]}</span>
            <span class="fop">&times;</span>
            <span class="fterm hot">the number above</span>
          </div>
          <div class="frow why">
            <span class="fterm"></span><span class="fop"></span>
            <span class="fterm">a rate I chose</span>
            <span class="fop"></span>
            <span class="fterm">how wrong it was</span>
            <span class="fop"></span>
            <span class="fterm">what this weight
              contributed</span>
          </div>
        </div>
        <p class="lbl fragment" data-fragment-index="6">
          {esc(trace["target_text"])} is now
          {trace["target_p_after"] * 100:.1f}%
        </p>
      </div>
    </div>
    <p class="cap fragment" data-fragment-index="6">
      Every weight moves the way that would have raised
      {esc(trace["target_text"])}'s score.
      <strong>The sign of each change is the sign of its incoming
      number.</strong>
    </p>
  </div>"""


# Which words are actually related is a human judgement, so the pairs below are
# chosen by hand rather than derived. Their identifiers are looked up from the
# real vocabulary, so if the corpus changes and a word moves, this breaks
# loudly instead of quietly showing a wrong number.
ID_PAIRS = [
    (["ZX80", "ZX81"], "next to each other, and related", True),
    (["APPLE", "ARCHIMEDES"], "next to each other, and not", False),
    (["APPLE", "LISA", "MACINTOSH"], "one company, scattered", False),
]


def figure_identifiers(vocabulary: list[str]) -> str:
    """An identifier is a name, not a description. You cannot do sums on it."""
    groups = []
    for n, (words, note, related) in enumerate(ID_PAIRS):
        chips = "".join(
            f'<span class="idchip"><span class="idn">'
            f"{vocabulary.index(w)}</span>{esc(w)}</span>"
            for w in words
        )
        mark = "yes" if related else "no"
        groups.append(
            f'<div class="idrow fragment" data-fragment-index="{n + 1}">'
            f'<span class="idset">{chips}</span>'
            f'<span class="idnote {mark}">{note}</span></div>'
        )

    return f"""
  <div class="fig ids">
    <div class="idrow">
      <span class="idset">
        <span class="idchip big"><span class="idn">
          {vocabulary.index("COMMODORE")}</span>COMMODORE</span>
      </span>
      <span class="idnote">thirteenth word in the alphabet. That is all
        thirteen means.</span>
    </div>
    {"".join(groups)}
    <p class="cap fragment" data-fragment-index="4">
      The identifier is a name, not a description.
      <strong>Nothing can be learned from doing arithmetic on it.</strong>
    </p>
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
      A token could have been a character instead. That model needs
      <strong>{rejected["multiplies"]:,}</strong> multiplies:
      {rejected["floor_seconds"]:.0f} seconds of bare MUL instructions against a
      {trace["budget_seconds"]}-second budget. I built it first, and
      rejected it.
    </p>
    <p class="cap fragment" data-fragment-index="2">
      Choosing how wide to make this, 6 would have fit our
      {trace["budget_seconds"]} second budget too, but I chose 3 to see how
      that would go. How small I could make it, and still be useful.
    </p>
  </div>"""


def figure_parameters(trace: dict) -> str:
    """What a parameter is, counted out. The word everyone has heard."""
    rows = []
    for n, part in enumerate(trace["parts"]):
        terms = '<span class="op">&times;</span>'.join(
            f'<span class="term"><span class="tn">{value}</span>'
            f'<span class="tl">{label}</span></span>'
            for value, label in zip(part["terms"], part["labels"])
        )
        rows.append(
            f'<div class="prow fragment" data-fragment-index="{n + 1}">'
            f'<span class="terms">{terms}</span>'
            f'<span class="op eq">=</span>'
            f'<span class="pcount">{part["count"]}</span>'
            f'<span class="pwhat">{esc(part["what"])}</span></div>'
        )

    return f"""
  <div class="fig params">
    <div class="ptable">
    {"".join(rows)}
    <div class="prow total fragment" data-fragment-index="4">
      <span class="terms"></span>
      <span class="op eq"></span>
      <span class="pcount">{trace["total"]}</span>
      <span class="pwhat">parameters</span>
    </div>
    </div>
    <p class="cap fragment" data-fragment-index="5">
      A parameter is one number that training is allowed to change.
      This model has {trace["total"]}.
      <strong>GPT-3 (2020) had 175B. DeepSeek-V3/R1 (2024) had
      671B.</strong>
    </p>
  </div>"""


def figure_loop(trace: dict, budget: dict, split: dict, names: int) -> str:
    """What it makes as the loop runs, and what the loop was budgeted to cost."""

    # Caption figures are computed, never typed, so they cannot disagree with
    # the columns above them.
    def pct(epoch, key):
        counted = trace["novelty"][str(epoch)]
        value = counted["drawn"] - counted["copied"] if key == "new" else counted[key]
        return round(100 * value / counted["drawn"])

    first_new = pct(trace["checkpoints"][0], "new")
    first_like = pct(trace["checkpoints"][0], "name_like")
    last_like = pct(trace["checkpoints"][-1], "name_like")

    # Two samples per checkpoint, always the same two, so nothing is picked
    # to suit the story. The second one is where the run turns.
    SHOW = (0, 2)
    rows = []
    for n, epoch in enumerate(trace["checkpoints"]):
        samples = trace["samples"][str(epoch)]
        classes = "epoch"
        note = ""
        if epoch == trace["chosen"]:
            classes += " chosen"
            note = "I stop here"
        elif epoch > trace["chosen"]:
            classes += " late"
        marks = []
        for i in SHOW:
            sample = samples[i]
            state = ""
            tag = ""
            if not sample["novel"]:
                state, tag = " copied", "in the corpus"
            elif sample["repeats"]:
                state, tag = " repeats", "repeats"
            marks.append(
                f'<div class="out{state}">{esc(sample["text"])}'
                + (f'<span class="tag">{tag}</span>' if tag else "")
                + "</div>"
            )
        shown = "".join(marks)
        counted = trace["novelty"][str(epoch)]
        drawn = counted["drawn"]
        new_pct = round(100 * (drawn - counted["copied"]) / drawn)
        like_pct = round(100 * counted["name_like"] / drawn)
        both_pct = round(100 * counted["both"] / drawn)
        # Only the column that matters is coloured, and only where it is
        # actually good. Novelty on its own rewards the untrained model, which
        # invents constantly and never produces a name.
        rows.append(
            f'<div class="{classes} fragment" data-fragment-index="{n}">'
            f'<span class="n">epoch {epoch}</span>'
            f'<div class="outs">{shown}</div>'
            f'<span class="novel">{new_pct}%</span>'
            f'<span class="novel">{like_pct}%</span>'
            f'<span class="novel {"good" if both_pct >= 80 else "poor"}">'
            f"{both_pct}%</span>"
            f'<span class="enote">{note}</span></div>'
        )

    return f"""
  <div class="fig">
    <div class="epochs">
      <div class="epoch head">
        <span class="n"></span><div class="outs"></div>
        <span class="novel">new</span>
        <span class="novel">right shape</span>
        <span class="novel">both</span>
        <span class="enote"></span>
      </div>
      {"".join(rows)}
    </div>
    <p class="cap rubric">
      New means the whole name is not one of the {names} in the corpus, word
      for word. Right shape means two to four tokens starting with one of the
      six makers in the corpus.
    </p>
    <p class="cap invent fragment" data-fragment-index="5">
      Epoch by epoch, same arithmetic, same {split["weights"]} bytes of weights.
      Early on it says the same token twice. By {trace["chosen"]} it picks
      different tokens that sit together plausibly. By {trace["epochs"]} it
      hands back what it was given. SINCLAIR never made an AMIGA.
    </p>
    <p class="cap fragment" data-fragment-index="6">
      New is not the same as good. Epoch 0 is {first_new}% new and
      {first_like}% the right shape; epoch {trace["epochs"]} is {last_like}%
      the right shape because they <em>are</em> the real names.
      <strong>Only the last column counts, and training past
      {trace["chosen"]} does not raise it.</strong>
    </p>
  </div>"""


def figure_draw(trace: dict, tokens: int) -> str:
    """How the next token is picked: one byte against a line of 256."""
    total = trace["total"]
    first, second = trace["walks"]
    ordinal = ["1st token", "2nd token", "3rd token", "4th token", "5th token", "6th token"]

    def line(step: dict) -> str:
        cells = []
        for s in step["stretches"]:
            width = 100 * s["share"] / total
            # Only a stretch wide enough to hold its name gets one; the
            # slivers are the 1-in-256 tokens and stay unlabelled but present.
            label = esc(s["text"]) if s["share"] >= 14 else ""
            cls = " hit" if s["hit"] else ""
            cells.append(
                f'<span class="dseg{cls}" style="width:{width:.3f}%">{label}</span>'
            )
        mark = 100 * (step["draw"] + 0.5) / total
        return (
            '<span class="dline">'
            + "".join(cells)
            + f'<span class="dmark" style="left:{mark:.3f}%">{step["draw"]}</span>'
            + "</span>"
        )

    rows = []
    for n, step in enumerate(first["steps"]):
        rows.append(
            f'<div class="drow fragment" data-fragment-index="{n + 1}">'
            f'<span class="dlab">{ordinal[n]}</span>'
            f"{line(step)}"
            f'<span class="dres"><span class="dtok">{esc(step["chosen"])}</span>'
            f'<span class="dshare">{step["share"]} of {total}</span></span>'
            "</div>"
        )
    after_rows = len(first["steps"]) + 1
    draws = lambda walk: ", ".join(str(s["draw"]) for s in walk["steps"])
    return f"""
  <div class="fig draw">
    <p class="cap top">The softmax turns the {tokens} scores into probabilities that add up
      to {total}, so every token owns a stretch of a line from 0 to {total - 1} as
      wide as its share.
      <strong>The machine draws one byte, and the token under it is the
      answer.</strong></p>
    <div class="dwalk">
      <div class="drow head"><span class="dlab"></span><span class="dline axis"><span class="dtick">0</span><span class="dtick">{total - 1}</span></span><span class="dres"></span></div>
      {"".join(rows)}
    </div>
    <p class="cap rule">For the first {trace["minimum_tokens"]} tokens END's stretch is handed to the
      favourite, so a name is never one word.</p>
    <p class="cap fragment" data-fragment-index="{after_rows}">
      Seed {first["seed"]} drew {draws(first)}: <strong>{esc(first["text"])}</strong>, the
      first name on the CoCo's screen. Seed {second["seed"]} drew {draws(second)} from
      the same table: <strong>{esc(second["text"])}</strong>.
    </p>
    <p class="cap fragment" data-fragment-index="{after_rows + 1}">
      Greedy decoding skips the draw and takes the widest stretch every time.
      That is what temperature zero means.
    </p>
  </div>"""


def figure_chip(trace: dict) -> str:
    """What the 6309 measured: EXP-014's rows on silicon, and what they cost."""
    rows = "".join(
        f'<div class="wrow"><span class="c what">{esc(r["what"])}</span>'
        f'<span class="c n">{r["ticks"]}</span>'
        f'<span class="c">{r["cycles_each"]:.0f}</span>'
        f'<span class="c n">{r["speedup"]:.2f}x</span></div>'
        for r in trace["rows"]
    )
    k = trace["kernel"]
    r1, r3 = trace["rates"]["coco1"], trace["rates"]["coco3"]
    return f"""
  <div class="fig why chip">
    <div class="wtable">
      <div class="wrow head">
        <span class="c what">what ran</span>
        <span class="c">ticks</span>
        <span class="c">cycles per<br>multiply</span>
        <span class="c">against<br>the 6809</span>
      </div>
      {rows}
    </div>
    <p class="cap">Ticks of the 60 Hz frame counter over {trace["multiplications"]:,}
      multiplies of the trained model's own weights, measured on the
      {trace["machine"]} on {trace["measured_on"]}. Every row computed the same
      checksum as the reference.</p>
    <p class="cap fragment" data-fragment-index="1">
      The sign correction from block 3 is not faster on the 6309. It is gone.
      MULD multiplies signed numbers, so {k["6809_instructions"]} instructions
      and {k["6809_cycles"]} cycles become {k["6309_instructions"]} and
      {k["6309_cycles"]}.
    </p>
    <p class="cap fragment" data-fragment-index="2">
      Its extra registers were worth about {trace["registers_gain_percent"]}%
      on the music loop, so that rewrite was never built.
      <strong>The instruction mattered. The registers did not.</strong>
    </p>
    <p class="cap fragment" data-fragment-index="3">
      What you just heard ran on that chip, in native mode at {r3["clock"]}:
      {r3["hz"]:,} samples a second. The CoCo 1 build plays the same tune at
      {r1["hz"]:,}.
    </p>
  </div>"""


def figure_cost(budget: dict, split: dict) -> str:
    """What the two choices cost in time and in memory."""
    return f"""
  <div class="fig">
    <div class="budget">
      <div class="brow fragment" data-fragment-index="1">
        <span class="bkind">time</span>
        <span class="bsum">{budget["epochs"]} epochs
          <span class="op">&times;</span> {budget["examples"]} examples
          <span class="op">&times;</span> {budget["per_example"]} multiplies</span>
        <span class="bval">{budget["multiplies"]:,}</span>
        <span class="bnote">multiplies, and
          {budget["instructions"] / 1e6:.1f} million instructions for the
          whole run</span>
      </div>
      <div class="brow fragment" data-fragment-index="2">
        <span class="bkind">to use</span>
        <span class="bsum">{split["use_only"]} inference
          <span class="op">+</span> {split["shared"]:,} shared
          <span class="op">+</span> {split["weights"]} weights</span>
        <span class="bval">{split["to_use"]:,}</span>
        <span class="bnote">bytes to run the finished model</span>
      </div>
      <div class="brow fragment" data-fragment-index="3">
        <span class="bkind">to learn</span>
        <span class="bsum">training loop
          <span class="op">+</span> corpus
          <span class="op">+</span> progress display</span>
        <span class="bval">+{split["learn_only"]}</span>
        <span class="bnote">bytes more, and none of it is needed once the
          model is trained</span>
      </div>
    </div>
    <p class="cap fragment" data-fragment-index="4">
      Neither number is special. I picked them so this would finish in a
      reasonable time and leave room for other code or graphics.
    </p>
    <p class="cap fragment" data-fragment-index="5">
      Still wouldn't fit on a {budget["baseline_bytes"] // 1024}K machine,
      but it's in the ballpark.
    </p>
  </div>"""


def figure_shift(shift: dict) -> str:
    """What the eight shift instructions do to the bits of a real gradient."""
    rows = []
    for n, step in enumerate(shift["steps"]):
        bits = step["bits"]
        # The bit riding the carry this row is B's new top bit: ASRA dropped
        # it out of A, RORB collected it. The gradient row has not shifted
        # yet, so its carry cell stays empty.
        carry = f"&rarr;{bits[8]}&rarr;" if n > 0 else ""
        cells = []
        for i, b in enumerate(bits):
            cells.append(
                f'<span class="bit{" on" if b == "1" else ""}'
                f"{' edge' if i == 7 else ''}"
                f'{" sign" if i == 0 else ""}">{b}</span>'
            )
            if i == 7:
                cells.append(f'<span class="carry">{carry}</span>')
        dropped = (
            ""
            if step["dropped"] is None
            else f'<span class="dropped">{step["dropped"]}</span>'
        )
        label = "gradient" if n == 0 else f"asra rorb &times;{n}"
        rows.append(
            f'<div class="bitrow{" last" if n == len(shift["steps"]) - 1 else ""}'
            f' fragment" data-fragment-index="{n}">'
            f'<span class="steplab">{label}</span>'
            f'<span class="bits">{"".join(cells)}</span>'
            f'<span class="carryout">{dropped}</span>'
            f'<span class="decimal">{step["value"]}</span></div>'
        )

    # The unsigned reading of the same bits, so the convention is stated
    # rather than assumed. It is also the number MUL would have produced.
    first = shift["steps"][0]
    unsigned = int(first["bits"], 2)
    return f"""
  <div class="fig shifts">
    <div class="bithead">
      <span class="steplab"></span>
      <span class="bits"><span class="bytelab">A &mdash; asra</span>
        <span class="carry">carry in</span>
        <span class="bytelab">B &mdash; rorb</span></span>
      <span class="carryout">carry out</span>
      <span class="decimal"></span>
    </div>
    <div class="bitrow signrow">
      <span class="steplab"></span>
      <span class="bits">{
        "".join(
            f'<span class="bit">{"&minus;" if i == 0 else ""}</span>'
            + ('<span class="carry"></span>' if i == 7 else "")
            for i in range(len(shift["steps"][0]["bits"]))
        )
    }</span>
      <span class="carryout"></span>
      <span class="decimal"></span>
    </div>
    {"".join(rows)}
    <p class="cap fragment" data-fragment-index="{len(shift["steps"])}">
      Two's complement: <strong>a leading 1 means negative.</strong> These
      same sixteen bits read as {unsigned:,} if you take them as unsigned.
    </p>
    <p class="cap fragment" data-fragment-index="{len(shift["steps"]) + 1}">
      <code>asra</code> keeps that top bit and drops the bottom one into the
      carry; <code>rorb</code> carries it in to B's top, then drops B's
      bottom bit into the same carry, uncollected: the
      <strong>carry out</strong>. Watch the left edge: <strong>the 1 copies
      itself downward, which keeps the value negative as it halves.</strong>
    </p>
    <p class="cap fragment" data-fragment-index="{len(shift["steps"]) + 2}">
      Every number in this model is a whole number, because this machine has
      no other kind. Effectively, we are doing
      <strong>quantization</strong> to 16 bits. The 4-bit models on phones
      make the same trade.
    </p>
    <p class="cap fragment" data-fragment-index="{len(shift["steps"]) + 3}">
      Four halvings is one multiplication by
      <strong>{1 / 2 ** (len(shift["steps"]) - 1)}</strong> &mdash; the
      nudge rate I chose for each training step. {first["value"]} times
      {1 / 2 ** (len(shift["steps"]) - 1)} is exactly
      {first["value"] / 2 ** (len(shift["steps"]) - 1)}; the shifts land on
      {shift["steps"][-1]["value"]}. That last carry out (the 1)
      is the 0.5 we lose in <strong>quantization</strong>.
    </p>
  </div>"""


def register_box(cells: list[str], word: str, extra: str = "") -> str:
    """One register or memory word as the trace draws it: byte cells side by
    side, and the number they compose in a bar beneath spanning both."""
    return (
        f'<div class="r16{extra}" style="--n:{len(cells)}">'
        f'{"".join(cells)}<span class="word">{word}</span></div>'
    )


def figure_sign(fix: dict) -> str:
    """Why one subtraction turns an unsigned product into a signed one:
    every number on the slide in binary, split at the byte, with the same
    two-bytes-over-a-value box the register trace uses beside it, so a
    reader can watch a decimal become its bits and its bits become two
    bytes."""

    def bits(value: int, width: int) -> str:
        pattern = format(value & ((1 << width) - 1), f"0{width}b")
        pad = "".join('<span class="bit gap"></span>' for _ in range(16 - width))
        cells = "".join(
            f'<span class="bit{" on" if b == "1" else ""}'
            f'{" edge" if i + (16 - width) == 7 else ""}">{b}</span>'
            for i, b in enumerate(pattern)
        )
        return f'<span class="bits">{pad}{cells}</span>'

    def box(value: int, width: int, word: str) -> str:
        if width == 8:
            cells = [f'<span class="byte">{value & 0xFF}</span>']
        else:
            cells = [
                f'<span class="byte">{(value >> 8) & 0xFF}</span>',
                f'<span class="byte">{value & 0xFF}</span>',
            ]
        return register_box(cells, word)

    factor, unsigned = fix["factor"], fix["unsigned_factor"]
    multiplier, raw = fix["multiplier"], fix["raw"]
    excess = (256 * multiplier) & 0xFFFF
    corrected, answer = fix["corrected"], fix["signed"]

    def row(
        index: int, label: str, value: int, width: int, word: str, note: str
    ) -> str:
        frag = f' class="fragment" data-fragment-index="{index}"' if index else ""
        return (
            f'<tr{frag}><td class="lab">{label}</td>'
            f'<td class="bitcell">{bits(value, width)}</td>'
            f'<td class="g">{box(value, width, word)}</td>'
            f'<td class="note">{note}</td></tr>'
        )

    rows = "".join(
        [
            row(
                0,
                f"the factor, {factor}",
                factor,
                8,
                str(factor),
                f"MUL ignores the sign bit and reads {unsigned}",
            ),
            row(
                1,
                f"MUL makes {unsigned} &times; {multiplier}",
                raw,
                16,
                str(raw),
                f"too big by 256 &times; {multiplier}",
            ),
            row(
                2,
                f"the excess, 256 &times; {multiplier}",
                excess,
                16,
                str(excess),
                f"{multiplier} in the high byte, nothing below",
            ),
            row(
                3,
                f"suba takes {multiplier} off the high byte",
                corrected,
                16,
                str(answer),
                f"{factor} &times; {multiplier} = {answer}",
            ),
        ]
    )
    return f"""
  <div class="fig sign2">
    <table class="signtbl">
      <thead><tr><th></th><th class="bitcell"><span class="bits">
        <span class="bytelab">high byte</span><span class="bytelab">low byte</span>
      </span></th><th class="g"><div class="r16 hdr" style="--n:2"><span class="lab">hi</span><span class="lab">lo</span><span class="word"></span></div></th><th></th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    <p class="cap fragment" data-fragment-index="4">
      The low byte is the same before and after. The excess lived only in
      the high byte, so one subtraction there is the whole fix.
    </p>
  </div>"""


def check_excerpt(excerpt: dict, mnemonics: list[str]) -> None:
    """Refuse on drift: each walked row names the instruction it describes.
    If the source moves and the excerpt no longer matches, the walk no
    longer describes the code, so stop rather than splice a table that
    quietly lies."""
    lines = excerpt["lines"]
    if len(lines) != len(mnemonics):
        raise SystemExit(
            f"{excerpt['title']}: {len(lines)} lines, {len(mnemonics)} rows"
        )
    for line, mnemonic in zip(lines, mnemonics):
        if not line["text"].strip().startswith(mnemonic):
            raise SystemExit(
                f"{excerpt['title']}: expected {mnemonic!r}, found {line['text']!r}"
            )


def signed(value: int, bits: int) -> int:
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


# A register trace is a table: one row per instruction, one column per byte,
# with the bytes of a 16-bit thing drawn as two touching cells under one
# header. D is A beside B; a 16-bit memory word is hi beside lo. That is the
# whole picture of how A and B compose into D, drawn the same way every time.
#
# groups: [(header, [(cell key, cell label), ...], show value)]
# rows:   [(mnemonic or None for the elided entry row,
#           {cell key: byte}, {written cell keys}, {groups whose value shows},
#           note, {read cell keys})]
# A note rides the boundary with its instruction. A note about the state
# the row shows is given as ("state", text) and stays level with the row.
# Each row is a snapshot of the bytes between two instructions, and the
# instruction is drawn on the boundary: between the state it read and the
# state it left. A byte it reads is lit navy in the row above it, a byte it
# writes amber in the row below; a cell that is both (written by the
# instruction above, read by the one below) is amber with a navy ring.
TWO_MUL_GROUPS = [
    ("D", [("A", "A"), ("B", "B")], True),
    ("factor", [("f", "")], True),
    ("at X", [("xh", "hi"), ("xl", "lo")], True),
    ("product", [("ph", "hi"), ("pl", "lo")], True),
]


def trace_two_muls(context_value: int, error: int) -> list[tuple]:
    """Walk the captured training multiply, byte by byte. The inputs are the
    same captured update the shift figure uses, so the product this walk
    ends on is the gradient that figure divides."""
    operand = error & 0xFFFF
    high, low = operand >> 8, operand & 0xFF
    first = context_value * low
    second = context_value * high
    b_after_add = ((second & 0xFF) + (first >> 8)) & 0xFF
    product = (b_after_add << 8) | (first & 0xFF)
    assert signed(product, 16) == context_value * error, "walk disagrees"
    st = {"A": context_value, "xh": high, "xl": low}
    rows = [("multiply_s8_s16", dict(st), set(), {"at X"}, "on arrival", set())]

    def row(mnemonic, read, written, values=(), note="", **changes):
        st.update(changes)
        rows.append((mnemonic, dict(st), set(written), set(values), note, set(read)))

    row("sta", {"A"}, {"f"}, {"factor"}, f=context_value)
    row("ldb", {"xl"}, {"B"}, B=low)
    row("mul", {"A", "B"}, {"A", "B"}, {"D"}, A=first >> 8, B=first & 0xFF)
    row("std", {"A", "B"}, {"ph", "pl"}, {"product"}, ph=first >> 8, pl=first & 0xFF)
    row("lda", {"f"}, {"A"}, A=context_value)
    row("ldb", {"xh"}, {"B"}, B=high)
    row("mul", {"A", "B"}, {"A", "B"}, {"D"}, A=second >> 8, B=second & 0xFF)
    row("addb", {"B", "ph"}, {"B"}, B=b_after_add)
    row(
        "stb",
        {"B"},
        {"ph"},
        {"product"},
        note=("state", f"{context_value} \u00d7 {error} = {signed(product, 16)}"),
        ph=b_after_add,
    )
    return rows


def trace_sign_fix(trace: dict) -> list[tuple]:
    """Walk the worked correction: the product's high byte, minus the
    multiplier's low byte, and the answer is signed."""
    raw_high, raw_low = trace["raw"] >> 8, trace["raw"] & 0xFF
    multiplier = trace["multiplier"] & 0xFFFF
    corrected_high = (raw_high - (multiplier & 0xFF)) & 0xFF
    st = {
        "f": trace["unsigned_factor"],
        "xh": multiplier >> 8,
        "xl": multiplier & 0xFF,
        "ph": raw_high,
        "pl": raw_low,
    }
    rows = [
        (
            None,
            dict(st),
            {"f", "xh", "xl", "ph", "pl"},
            {"factor", "at X", "product"},
            (
                f"the MULs saw {trace['unsigned_factor']}, not {trace['factor']}: "
                f"{trace['unsigned_factor']} \u00d7 {trace['multiplier']} = {trace['raw']}"
            ),
            set(),
        )
    ]

    def row(mnemonic, read, written, values=(), note="", **changes):
        st.update(changes)
        rows.append((mnemonic, dict(st), set(written), set(values), note, set(read)))

    row("tst", {"f"}, set(), note="negative")
    row("bpl", set(), set(), note="no branch")
    row("lda", {"ph"}, {"A"}, A=raw_high)
    row("suba", {"A", "xl"}, {"A"}, A=corrected_high)
    row(
        "sta",
        {"A"},
        {"ph"},
        {"product"},
        note=(
            "state",
            f"{trace['factor']} \u00d7 {trace['multiplier']} = {trace['signed']}",
        ),
        ph=corrected_high,
    )
    assert signed((corrected_high << 8) | raw_low, 16) == trace["signed"]
    return rows


# The shift slide only needs the value: the next slide draws the bits and
# the carry. One wide cell holds D as a signed number, filled after each
# ASRA/RORB pair.
SHIFT_GROUPS = [("D", [("d", "")], False, " plain")]


def trace_learning_rate(shift: dict) -> list[tuple]:
    """Walk the captured gradient through the four shift pairs, showing the
    value after each pair: halved, rounding toward minus infinity."""
    steps = shift["steps"]
    rows = [("lbsr", {"d": steps[0]["value"]}, {"d"}, set(), "", set())]
    for step in steps[1:]:
        rows.append(("asra", {}, set(), set(), "", set()))
        rows.append(("rorb", {"d": step["value"]}, {"d"}, set(), "", set()))
    assert steps[-1]["value"] == steps[0]["value"] >> 4, "four halvings is >> 4"
    return rows


def figure_register_trace(
    excerpt: dict,
    note: str,
    groups: list[tuple],
    rows: list[tuple],
    legend: bool = True,
    offset: bool = True,
) -> str:
    """One assembly excerpt beside its register trace: after every
    instruction, every byte the walk follows, with the bytes that
    instruction wrote lit and a 16-bit value printed where two cells
    compose into one number."""
    rows = [r if len(r) == 6 else (*r, set()) for r in rows]
    walked = [r for r in rows if r[0] is not None]
    check_excerpt(excerpt, [r[0] for r in walked])
    if rows[0][0] is not None and excerpt["begins_inside"]:
        rows = [(None, {}, set(), set(), "", set())] + rows
    elif rows[0][0] is None and not excerpt["begins_inside"]:
        raise SystemExit(f"{excerpt['title']}: entry row without elided lines")
    lines = iter(excerpt["lines"])

    head1 = '<th class="ct"></th>'
    head2 = '<th class="ct"></th>'
    groups = [g if len(g) == 4 else (*g, "") for g in groups]
    for header, cells, value, extra in groups:
        head1 += f'<th class="grp">{esc(header)}</th>'
        labels = [f'<span class="lab">{esc(label)}</span>' for _, label in cells]
        if "plain" in extra:
            head2 += '<th class="g"></th>'
        else:
            head2 += f'<th class="g">{register_box(labels, "", " hdr" + extra)}</th>'
    head1 += '<th class="note"></th>'
    head2 += (
        '<th class="note legend"><span class="byte r">read</span>'
        '<span class="byte w">written</span></th>'
        if legend
        else '<th class="note"></th>'
    )

    # What an instruction reads lights the snapshot before it, which is the
    # previous row.
    reads_above = [set() for _ in rows]
    for i, (_, _, _, _, _, read) in enumerate(rows):
        if i > 0:
            reads_above[i - 1] |= read

    body = ""
    for i, (mnemonic, state, written, values, text, _) in enumerate(rows):
        read = reads_above[i]
        if mnemonic is None:
            cls, code = "elide", "..."
        else:
            line = next(lines)
            # A label sits in column one of the source. It is an anchor, not
            # an instruction: nothing runs there, so it sits level with the
            # state the CPU arrives with rather than between two states.
            is_label = not line["text"][:1].isspace()
            cls = "label" if is_label else ("hot" if line["hot"] else "")
            code = re.sub(r"\s+", "  ", line["text"].strip())
        if not state:
            cls += " empty"
        if isinstance(text, tuple):
            cls += " statenote"
            text = text[1]
        cells_html = ""
        if not state:
            cells_html = '<td class="g"></td>' * len(groups)
            groups_here = []
        else:
            groups_here = groups
        for header, cells, value, extra in groups_here:
            bytes_ = [state.get(key) for key, _ in cells]
            if "plain" in extra:
                shown = "" if bytes_[0] is None else bytes_[0]
                cells_html += f'<td class="g plain">{shown}</td>'
                continue
            spans = [
                '<span class="byte'
                + (" w" if key in written else "")
                + (" r" if key in read else "")
                + f'">{"" if byte is None else byte}</span>'
                for (key, _), byte in zip(cells, bytes_)
            ]
            word = ""
            if value and header in values and None not in bytes_:
                total = 0
                for byte in bytes_:
                    total = (total << 8) | byte
                word = str(signed(total, 8 * len(bytes_)))
            cells_html += f'<td class="g">{register_box(spans, word, ("" if value else " bare") + extra)}</td>'
        body += (
            f'<tr class="{cls.strip()}"><td class="ct"><div class="code">'
            f"{esc(code)}</div></td>{cells_html}"
            f'<td class="note"><div class="code">{esc(text)}</div></td></tr>'
        )
    return f"""
  <p class="lead">{esc(excerpt["title"])}</p>
  <div class="fig code trace">
    <table class="rtrace{"" if offset else " level"}">
      <thead><tr>{head1}</tr><tr>{head2}</tr></thead>
      <tbody>{body}</tbody>
    </table>
    <p class="cap">{note} <span class="src">{esc(excerpt["source"])}</span></p>
  </div>"""


def figure_code(excerpt: dict, note: str) -> str:
    """One assembly reveal, taken verbatim from the source that assembles."""
    lines = "".join(
        f'<div class="cline{" hot" if line["hot"] else ""}">{esc(line["text"])}</div>'
        for line in excerpt["lines"]
    )
    elided = '<div class="cline elide">...</div>' if excerpt["begins_inside"] else ""
    tail = '<div class="cline elide">...</div>' if excerpt["dropped_comments"] else ""
    return f"""
  <p class="lead">{esc(excerpt["title"])}</p>
  <div class="fig code">
    <pre class="asm">{elided}{lines}{tail}</pre>
    <p class="cap">{note} <span class="src">{esc(excerpt["source"])}</span></p>
  </div>"""


def figure_second_model(prompts: dict, first: dict, first_epochs: int) -> str:
    """EXP-005's vocabulary beside the first model's numbers: the machinery
    held, the reading material replaced, and almost no words in common."""

    def parameters(count: int) -> int:
        return 2 * count * 3 + count * 3 + count

    if parameters(len(prompts["tokens"])) != prompts["parameters"]:
        raise SystemExit("second model's parameter arithmetic drifted")
    survivors = set(prompts["tokens"]) & set(first["vocabulary"])
    chips = "".join(
        f'<div class="tok{" hot" if token in survivors else ""}">'
        f'<span class="id">{index}</span>{esc(token)}</div>'
        for index, token in enumerate(prompts["tokens"])
    )
    return f"""
  <div class="fig">
    <div class="vocab">{chips}</div>
    <p class="cap fragment" data-fragment-index="1">
      A different token model.
      <strong>The identifier is still just a word.</strong>
    </p>
    <p class="cap fragment" data-fragment-index="2">
      {len(first["vocabulary"])} tokens &rarr; {len(prompts["tokens"])}.
      {parameters(len(first["vocabulary"]))} parameters &rarr;
      {prompts["parameters"]}.
      {first["examples"]} examples &rarr; {prompts["examples"]}.
      {first_epochs} epochs &rarr; {prompts["epochs"]}.
      <strong>Different token mappings, same code.</strong>
    </p>
    <p class="cap fragment" data-fragment-index="3">
      {prompts["epochs"]} epochs on eight lines almost memorizes them:
      {sum(c["verbatim"] for c in prompts["completions"])} of the
      {len(prompts["completions"])} prompted completions are corpus lines,
      verbatim. Block 2 called that <strong>overfitting</strong>. Here it
      is the assignment: the room has to recognize the campaigns.
    </p>
  </div>"""


def figure_second_costs(prompts: dict, first_budget: dict) -> str:
    """The parameter count and the training bill, redone at this model's
    numbers. Deliberately the same two figures the room has already read
    once, so this time they can do the arithmetic themselves."""
    v = len(prompts["tokens"])
    ctx, emb = prompts["context"], prompts["embedding"]
    table_rows = (
        (
            [(str(ctx), "context window"), (str(v), "tokens"), (str(emb), "numbers")],
            ctx * v * emb,
            "a row for every window position and token",
        ),
        (
            [(str(v), "tokens"), (str(emb), "numbers")],
            v * emb,
            "a row for every token it can predict",
        ),
        ([(str(v), "tokens")], v, "one starting nudge per token"),
    )
    if sum(count for _, count, _ in table_rows) != prompts["parameters"]:
        raise SystemExit("second model's parameter rows drifted")
    prows = ""
    for terms, count, what in table_rows:
        spans = '<span class="op">&times;</span>'.join(
            f'<span class="term"><span class="tn">{n}</span>'
            f'<span class="tl">{label}</span></span>'
            for n, label in terms
        )
        prows += (
            f'<div class="prow"><span class="terms">{spans}</span>'
            f'<span class="op eq">=</span><span class="pcount">{count}</span>'
            f'<span class="pwhat">{what}</span></div>'
        )
    budget = prompts["budget"]
    ratio = budget["multiplies"] / first_budget["multiplies"]
    return f"""
  <div class="fig params">
    <div class="ptable">
    {prows}
    <div class="prow total">
      <span class="terms"></span>
      <span class="op eq"></span>
      <span class="pcount">{prompts["parameters"]}</span>
      <span class="pwhat">parameters</span>
    </div>
    </div>
    <div class="budget">
      <div class="brow fragment" data-fragment-index="1">
        <span class="bkind">time</span>
        <span class="bsum">{prompts["epochs"]} epochs
          <span class="op">&times;</span> {prompts["examples"]} examples
          <span class="op">&times;</span> {budget["per_example"]} multiplies</span>
        <span class="bval">{budget["multiplies"]:,}</span>
        <span class="bnote">multiplies, {ratio:.1f} times the first
          run</span>
      </div>
      <div class="brow fragment" data-fragment-index="2">
        <span class="bkind">space</span>
        <span class="bsum">{prompts["parameters"]} parameters
          <span class="op">&times;</span> {first_budget["bytes_each"]} bytes</span>
        <span class="bval">{budget["weight_bytes"]}</span>
        <span class="bnote">bytes of weights, up from
          {first_budget["bytes"]}</span>
      </div>
    </div>
    <p class="cap fragment" data-fragment-index="3">
      Two choices set the cost: vocabulary size and epoch count.
    </p>
  </div>"""


DATA = ROOT / "experiments" / "data"


def corpus_lines(filename: str) -> list[str]:
    path = DATA / filename
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def corpus_columns(lines: list[str], columns: int) -> str:
    """The lines chunked into vertical columns, reading down then across."""
    per = -(-len(lines) // columns)
    blocks = []
    for c in range(columns):
        entries = "".join(
            f'<div class="entry">{esc(line)}</div>'
            for line in lines[c * per : (c + 1) * per]
        )
        blocks.append(f'<div class="col">{entries}</div>')
    return "".join(blocks)


def figure_shape(dealt: list[str]) -> str:
    """One title's walk through the frame model, so "the shape" is a picture
    before it is a ledger row: a real title the model read, the shape left
    behind when the names lift out, and a dealt title where dictionary names
    fill the gaps. Both titles are real - the read row is a corpus line and
    the dealt row is on the demo screen - so the figure asserts them."""
    corpus = corpus_lines("EXP-012-tos-titles.txt")
    for premise in ("BALANCE OF TERROR", "JOURNEY TO BABEL"):
        if premise not in corpus:
            raise SystemExit(f"shape figure premise gone: {premise!r} not in corpus")
    if "BALANCE OF BABEL" not in dealt:
        raise SystemExit("shape figure premise gone: BALANCE OF BABEL not dealt")

    def row(label: str, title: str, note: str) -> str:
        return (
            f'<span class="slab">{label}</span>'
            f'<span class="stitle">{title}</span>'
            f'<span class="snote">{note}</span>'
        )

    name = '<span class="name">{}</span>'.format
    # The gap holds the lifted name in transparent ink, so the underline is
    # exactly as wide as the name that left and the OFs stack vertically.
    gap = '<span class="gap">{}</span>'.format
    rows = "".join(
        [
            row(
                "it read",
                f"{name('BALANCE')} OF {name('TERROR')}",
                "a real title, straight from the corpus",
            ),
            row(
                "it kept",
                f"{gap('BALANCE')} OF {gap('TERROR')}",
                "the names lift out. the shape stays",
            ),
            row(
                "it dealt",
                f"{name('BALANCE')} OF {name('BABEL')}",
                "two dictionary names fill the gaps",
            ),
        ]
    )
    return f"""
  <div class="fig">
    <div class="shape">{rows}</div>
    <p class="cap">Every word is real &mdash; BABEL was lifted from JOURNEY
      TO BABEL, another real title. <strong>The title itself never
      existed.</strong></p>
  </div>"""


def figure_corpus(filename: str, shown: int, columns: int, note: str) -> str:
    """A model's reading material, quoted verbatim from the data file it
    trains on. One recognisable style for every corpus in the talk, with the
    count always honest about how much is on screen."""
    lines = corpus_lines(filename)
    picked = lines[:shown]
    caption = (
        note
        if shown >= len(lines)
        else f"The first {len(picked)} of {len(lines)} lines. {note}"
    )
    return f"""
  <div class="fig">
    <div class="corpus">{corpus_columns(picked, columns)}</div>
    <p class="cap">{caption}</p>
  </div>"""


def figure_melody_corpus() -> str:
    """The dance tunes as the melody model reads them: a token per sixteenth
    note. Drawn straight from the committed corpus file - title, mode and
    metre from the record, then the first bar's tokens with the demo's own
    glosses: a dot holds the note (token 32), R is a rest (token 33)."""
    import json as json_module

    path = ROOT / "experiments" / "data" / "EXP-010-dance.jsonl"
    tunes = [json_module.loads(line) for line in path.read_text().splitlines()]
    shown = tunes[:4]

    def gloss(token: int) -> str:
        if token == 32:
            return "&middot;"
        if token == 33:
            return "R"
        return str(token)

    rows = "".join(
        '<div class="tune">'
        f'<span class="tname">{esc(t["title"].split(" -- ")[0].upper())}</span>'
        f'<span class="tkey">{esc(t["mode"])} {esc(t["metre"])}</span>'
        f'<span class="ttok">{" ".join(gloss(k) for k in t["melody"][:16])}</span>'
        "</div>"
        for t in shown
    )
    trained = sum(1 for t in tunes if t["split"] == "train")
    return f"""
  <div class="fig">
    <div class="tunes">{rows}</div>
    <p class="cap">The first sixteen tokens of {len(shown)} of {len(tunes)}
      tunes: the number is how far the pitch sits above the home note, a dot
      holds it, R is a rest. It read {trained}; the other
      {len(tunes) - trained} were held back to test it.</p>
  </div>"""


def figure_corpora(sources: list[tuple[str, str]], shown: int, note: str) -> str:
    """Several corpora side by side, labelled - block 7's three corpora."""
    blocks = []
    for label, filename in sources:
        lines = corpus_lines(filename)[:shown]
        entries = "".join(f'<div class="entry">{esc(line)}</div>' for line in lines)
        blocks.append(
            f'<div class="col"><p class="lbl">{esc(label)}</p>{entries}</div>'
        )
    return f"""
  <div class="fig">
    <div class="corpus">{"".join(blocks)}</div>
    <p class="cap">The first {shown} lines of each collection.{" " + note if note else ""}</p>
  </div>"""


# One colour per maker, so the same maker is the same colour in every bar.
MAKER_CLASS = {"APPLE": "mk-a", "COMMODORE": "mk-c", "TANDY": "mk-t"}


def figure_bias(trace: dict) -> str:
    """Same everything, different data. Then same data, different order."""

    # Both bars are 14em wide, and a segment label that does not fit its
    # segment gets clipped mid-glyph, which reads as a rendering bug. So
    # every segment labels itself by what fits: the full "MAKER n" when the
    # segment is wide enough, the bare count when only that fits, nothing
    # when not even the count does (the interleave's stripes). 0.45em per
    # character is calibrated against the labels that render today.
    BAR_EM = 14.0

    def seg_span(css: str, full: str, short: str, share: float) -> str:
        budget = (BAR_EM * share / 100) / 0.45
        text = full if len(full) <= budget else (short if len(short) <= budget else "")
        return f'<span class="seg {css}" style="width:{share:.2f}%">{text}</span>'

    def read_bar(composition: list) -> str:
        # The training composition in the same colours as the output bar, so
        # cause and effect share one visual language. Labels are uniform
        # across the bar: equal segments with unequal labels read as if the
        # segments differed, so if any full label fails to fit, they all
        # drop to counts together.
        total = sum(count for _, count in composition)
        shares = [(maker, count, 100 * count / total) for maker, count in composition]
        fulls_fit = all(
            len(f"{maker} {count}") <= (BAR_EM * share / 100) / 0.45
            for maker, count, share in shares
        )
        return "".join(
            seg_span(
                MAKER_CLASS[maker],
                f"{maker} {count}" if fulls_fit else str(count),
                str(count),
                share,
            )
            for maker, count, share in shares
        )

    def row(run: dict, index: int, composition: list, note: str = "") -> str:
        segments = "".join(
            seg_span(
                MAKER_CLASS[maker],
                f"{maker} {run['counts'][maker]}",
                str(run["counts"][maker]),
                100 * run["counts"][maker] / run["total"],
            )
            for maker in trace["makers"]
            if run["counts"][maker]
        )
        if run["other"]:
            # The gray segment: draws that opened with some other vocabulary
            # word, no maker first.
            segments += seg_span(
                "mk-o",
                f"NONE {run['other']}",
                str(run["other"]),
                100 * run["other"] / run["total"],
            )
        return (
            f'<div class="brun fragment" data-fragment-index="{index}">'
            f'<span class="blab">{esc(run["label"].lower())}</span>'
            f'<span class="bbar">{read_bar(composition)}</span>'
            f'<span class="bbar">{segments}</span>'
            f'<span class="bsample">{esc(run["sample"])}</span>'
            f'<span class="bnote2">{note}</span></div>'
        )

    # Each run's training composition, in the order the model met it. The
    # single-fan corpora are one maker each; the concatenated corpus is the
    # three collections in file order (asserted below: the favourite it
    # produced is the last maker in that order); the interleaved corpus
    # cycles the makers name by name, drawn as the stripes it is. Counts
    # follow EXP-003, the fan-corpus bias runs: 18 names per collection.
    makers = trace["makers"]

    def single(run):
        return [(run["favourite"], run["names"])]

    per_maker_all = trace["runs"][3]["names"] // len(makers)
    concat_comp = [(maker, per_maker_all) for maker in makers]
    interleave_comp = [(maker, 1) for _ in range(per_maker_all) for maker in makers]

    fans = "".join(
        row(run, n + 1, single(run)) for n, run in enumerate(trace["runs"][:3])
    )
    concatenated, interleaved = trace["runs"][3], trace["runs"][4]

    # A stray draw renders as a sliver too thin to label itself, and an
    # unlabelled value on screen is a question from the audience. Name it,
    # from the data, on the same click as the row that shows it.
    strays = [
        (n + 1, run, maker, run["counts"][maker])
        for n, run in enumerate(trace["runs"][:3])
        for maker in trace["makers"]
        if maker != run["favourite"] and run["counts"][maker] > 0
    ]
    blip = ""
    if strays:
        clauses = " ".join(
            f"The thin slice in what the {esc(run['label'].lower())} wrote: "
            f"{count} draw{'' if count == 1 else 's'} of {run['total']} "
            f"came out {esc(maker)} anyway."
            for _, run, maker, count in strays
        )
        blip = (
            f'\n    <p class="lbl blip fragment" '
            f'data-fragment-index="{max(n for n, *_ in strays)}">'
            f"{clauses} The bias is a lean, not a wall, the words were "
            f"in the vocabulary.</p>"
        )

    # The concatenated run lands as a near-copy of the tandy fan's bar. That
    # is the finding, and unsaid it reads as a chart mistake - so say it, on
    # the same click, with the copy claim checked against the data and the
    # went-last claim checked against the maker order the corpus was laid in.
    tandy_fan = trace["runs"][2]
    is_copy = (
        concatenated["counts"] == tandy_fan["counts"]
        and concatenated["other"] == tandy_fan["other"]
    )
    last_maker = trace["makers"][-1]
    if concatenated["favourite"] != last_maker:
        raise SystemExit(
            "bias figure premise gone: concatenated favourite is "
            f"{concatenated['favourite']!r}, not the last maker {last_maker!r}"
        )
    per_maker = concatenated["names"] // len(trace["makers"])
    copy_note = (
        f'<p class="lbl blip fragment" data-fragment-index="4">'
        f"{per_maker} names per maker went in, balanced - and the bar comes "
        f"out {'a copy of' if is_copy else 'nearly a copy of'} what the "
        f"{esc(tandy_fan['label'].lower())} wrote. {esc(last_maker)}'s names "
        f"went last in the file, and last is what stuck.</p>"
    )

    # The row labels name training data; the bars show generated output. The
    # header row says so, on screen, before the first bar lands - without it
    # the figure reads as a chart about the data and the journey from corpus
    # to output happens only in the speaker notes.
    header = (
        '<div class="brun bhead">'
        '<span class="blab"></span>'
        '<span class="bh">what it read</span>'
        f'<span class="bh">the {trace["samples"]} names it wrote, '
        "by first word</span>"
        '<span class="bh">one of the 20</span>'
        '<span class="bh"></span></div>'
    )

    return f"""
  <div class="fig bias">
    {header}
    <p class="lbl">one collection each</p>
    {fans}{blip}
    <p class="lbl fragment" data-fragment-index="4">
      the same {concatenated["names"]} names, balanced, in two orders
    </p>
    {row(concatenated, 4, concat_comp, "end to end")}
    {copy_note}
    {row(interleaved, 5, interleave_comp, "shuffled together")}
    <p class="cap fragment" data-fragment-index="6">
      Held fixed throughout: the architecture, the starting numbers, the
      training budget, the vocabulary, the sampling seeds.
      <strong>Nobody chose to make the fourth one a Tandy fan. Laying the
      collections end to end did it.</strong>
    </p>
  </div>"""


def figure_changed(spec: dict) -> str:
    """Held, then changed. The same shape every time the talk changes one thing.

    The three "change one thing" slides used to name the change without showing
    it. What stayed fixed matters as much as what moved: a before-and-after
    with no controls beside it is an anecdote, so the controls are on the slide
    rather than in the narration.
    """
    held = '<span class="hsep">&middot;</span>'.join(
        f"<span>{esc(item)}</span>" for item in spec["held"]
    )
    rows = "".join(
        f'<div class="ba fragment" data-fragment-index="{n + 1}">'
        f'<span class="balab">{esc(label)}</span>'
        f'<span class="bfrom">{esc(before)}</span>'
        f'<span class="barrow">&rarr;</span>'
        f'<span class="bto">{esc(after)}</span></div>'
        for n, (label, before, after) in enumerate(spec["pairs"])
    )
    return f"""
  <div class="fig changed">
    <p class="held"><span class="hlead">held fixed</span>{held}</p>
    <div class="deltas">{rows}</div>
    <p class="cap fragment" data-fragment-index="{len(spec["pairs"]) + 1}">
      {spec["note"]}</p>
  </div>"""


def splice(source: str, name: str, body: str) -> str:
    pattern = re.compile(
        rf"(<!-- FIGURE:{re.escape(name)} -->).*?(<!-- /FIGURE:{re.escape(name)} -->)",
        re.DOTALL,
    )
    if not pattern.search(source):
        raise SystemExit(f"no marker region for figure {name!r} in the deck")
    return pattern.sub(lambda m: f"{m.group(1)}{body}\n  {m.group(2)}", source)


def refuse_to_eat_hand_edits() -> None:
    """Splicing overwrites every FIGURE region, so uncommitted deck edits may
    include hand-written caption changes this run would silently destroy.
    That has happened. Commit the deck first (porting any figure-region edits
    into this file), or pass --anyway to splice regardless.

    Even --anyway prints the dirty diff before splicing. That has also been
    needed: an --anyway run once erased a hand edit nobody had read, and the
    only copy left was in an editor's undo buffer. Printed, the edit at least
    survives in the terminal scrollback and the session log."""
    try:
        dirty = (
            subprocess.run(
                ["git", "diff", "--quiet", "--", str(DECK)],
                cwd=ROOT,
                check=False,
            ).returncode
            != 0
        )
    except OSError:
        return
    if dirty and "--anyway" in sys.argv:
        print("splicing over uncommitted deck changes; the diff, for the record:")
        subprocess.run(
            ["git", "--no-pager", "diff", "--", str(DECK)], cwd=ROOT, check=False
        )
        return
    if dirty:
        raise SystemExit(
            f"{DECK.relative_to(ROOT)} has uncommitted changes, which may be "
            "hand edits inside FIGURE regions that splicing would erase.\n"
            "Commit the deck first (port any figure-region edits into "
            "make_deck_figures.py), or re-run with --anyway."
        )


def main() -> None:
    refuse_to_eat_hand_edits()
    traces = json.loads(TRACES.read_text())
    code = json.loads((TRACES.parent / "code.json").read_text())
    bias = json.loads((TRACES.parent / "bias.json").read_text())
    prompts = json.loads((TRACES.parent / "prompts.json").read_text())

    # Block 4. Every value here is from one trained model in one run, so
    # "the same model" is true by construction.
    by_prompt = {c["prompt"]: c["completion"] for c in prompts["completions"]}
    prompt_change = {
        "held": [
            f"the model, all {prompts['parameters']} of its numbers",
            f"checksum {prompts['checksum']}, before and after",
            "seed 6809, greedy decoding",
        ],
        "pairs": [
            ("asked nothing", "", prompts["unprompted"]),
            ("asked", "I ADORE", by_prompt["I ADORE"]),
            ("asked", "ARE YOU", by_prompt["ARE YOU"]),
            ("asked", "THE COMPUTER", by_prompt["THE COMPUTER"]),
        ],
        "note": "The prompt is just the first few tokens of the output.",
    }

    # Block 5 moved to EXP-007, the all-RAM sentence completer, whose size
    # comparison is hand-authored in the deck from recorded results. EXP-011,
    # the context-editing attention head, now demonstrates at the table.
    vocabulary = traces["vocabulary"]["vocabulary"]

    deck = DECK.read_text()
    deck = splice(deck, "vocabulary", figure_vocabulary(traces["vocabulary"]))
    deck = splice(deck, "tables", figure_tables(traces["step"]))
    deck = splice(deck, "step", figure_step(traces["step"], vocabulary))
    deck = splice(
        deck,
        "corpus2",
        figure_corpus(
            "EXP-002-tokenized-computer-names.txt",
            18,
            2,
            "These are the facts we feed it for training.",
        ),
    )
    deck = splice(
        deck,
        "corpus4",
        figure_corpus(
            "EXP-005-marketing-language.txt",
            8,
            1,
            "Eighty epochs over eight lines is why it almost memorizes them.",
        ),
    )
    deck = splice(
        deck,
        "corpus5",
        figure_corpus(
            "EXP-007-sentence-training.txt",
            8,
            1,
            "The 248 vocabulary slots come from sentences like these.",
        ),
    )
    deck = splice(deck, "melodycorpus", figure_melody_corpus())
    dealt_titles = json.loads((TRACES.parent / "titles.json").read_text())
    deck = splice(deck, "shape", figure_shape(dealt_titles["dealt"]))
    deck = splice(
        deck,
        "corpus6",
        figure_corpus(
            "EXP-012-tos-titles.txt", 12, 2, "All of them are real episode titles."
        ),
    )
    deck = splice(
        deck,
        "corpus7",
        figure_corpora(
            [
                ("apple fan", "EXP-003-apple-fan.txt"),
                ("commodore fan", "EXP-003-commodore-fan.txt"),
                ("tandy fan", "EXP-003-tandy-fan.txt"),
            ],
            6,
            "",
        ),
    )
    deck = splice(deck, "ids", figure_identifiers(vocabulary))
    deck = splice(deck, "why", figure_why_three(traces["why_three"]))
    deck = splice(deck, "params", figure_parameters(traces["parameters"]))
    deck = splice(
        deck,
        "loop",
        figure_loop(
            traces["loop"],
            traces["budget"],
            traces["split"],
            traces["vocabulary"]["names"],
        ),
    )
    deck = splice(deck, "cost", figure_cost(traces["budget"], traces["split"]))
    deck = splice(deck, "draw", figure_draw(traces["draw"], len(traces["vocabulary"]["vocabulary"])))
    deck = splice(deck, "chip", figure_chip(traces["chip"]))
    deck = splice(deck, "bias", figure_bias(bias))
    deck = splice(
        deck,
        "vocab5",
        figure_second_model(prompts, traces["vocabulary"], traces["budget"]["epochs"]),
    )
    deck = splice(deck, "params5", figure_second_costs(prompts, traces["budget"]))
    deck = splice(deck, "promptchange", figure_changed(prompt_change))
    shift = json.loads((TRACES.parent / "shift.json").read_text())
    captured = shift["source"]
    deck = splice(
        deck,
        "twomuls",
        figure_register_trace(
            code["two_muls"],
            "The 6809 multiplies two unsigned bytes. Two of those make one "
            "signed multiply. The values are one real training step: context "
            f"{captured['context_value']} times error {captured['error']}.",
            TWO_MUL_GROUPS,
            trace_two_muls(captured["context_value"], captured["error"]),
        ),
    )
    deck = splice(
        deck,
        "signfix",
        figure_register_trace(
            code["sign_fix"],
            "The first slide's factor was positive, so it skipped this. Here the "
            f"factor is {traces['sign_fix']['factor']}. MUL cannot take a negative "
            f"byte and sees {traces['sign_fix']['unsigned_factor']}, which is 256 "
            "too many, so the product is 256 times the multiplier too large. One "
            "subtraction takes that out. The pair is chosen, not captured, and "
            "sits inside the range the training run measured.",
            TWO_MUL_GROUPS,
            trace_sign_fix(traces["sign_fix"]),
        ),
    )
    deck = splice(deck, "signbits", figure_sign(traces["sign_fix"]))
    deck = splice(deck, "shiftbits", figure_shift(shift))
    deck = splice(
        deck,
        "lrcode",
        figure_register_trace(
            code["learning_rate"],
            "Each ASRA and RORB pair halves the signed number. Four pairs divide "
            "by sixteen, and that is the learning rate. It picks up the "
            f"{captured['gradient']} the multiply slide made.",
            SHIFT_GROUPS,
            trace_learning_rate(shift),
            legend=False,
            offset=False,
        ),
    )
    DECK.write_text(deck, encoding="utf-8")
    count = deck.count("<!-- FIGURE:")
    print(f"spliced {count} figures into presentation/deck/index.html")


if __name__ == "__main__":
    main()
