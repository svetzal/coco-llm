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
        f'<span class="num moved">{v:+.4f}</span>'
        for v in trace["vector_display"]
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
            <span class="fterm">a rate we chose</span>
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
            f'{vocabulary.index(w)}</span>{esc(w)}</span>'
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
      <strong>GPT-3 had {trace["gpt3"]:,}.</strong>
      Same word, same meaning.
    </p>
  </div>"""


def figure_loop(trace: dict, budget: dict, split: dict) -> str:
    """What it makes as the loop runs, and what the loop was budgeted to cost."""
    # Caption figures are computed, never typed, so they cannot disagree with
    # the columns above them.
    def pct(epoch, key):
        counted = trace["novelty"][str(epoch)]
        value = (
            counted["drawn"] - counted["copied"] if key == "new" else counted[key]
        )
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
            note = "we stop here"
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
            f'{both_pct}%</span>'
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
      Right shape means two to four tokens starting with one of the six makers
      in the corpus. It is a structure check, not a judgement:
      <em>TANDY TANDY TANDY</em> would pass.
    </p>
    <p class="cap invent fragment" data-fragment-index="5">
      Same machine, same arithmetic, same {split["weights"]} bytes of weights.
      Early on it says the same token twice. By {trace["chosen"]} it picks
      different tokens that sit together plausibly. By {trace["epochs"]} it
      hands back what it was given.
      <strong>SINCLAIR never made an AMIGA. It knows which tokens follow
      which, and nothing else.</strong>
    </p>
    <p class="cap fragment" data-fragment-index="6">
      New is not the same as good. Epoch 0 is {first_new}% new and
      {first_like}% the right shape; epoch {trace["epochs"]} is {last_like}%
      the right shape because they <em>are</em> the real names.
      <strong>Only the last column counts, and training past
      {trace["chosen"]} does not raise it.</strong>
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
      Neither number is magic. Both were chosen so this would finish in a
      reasonable time and leave room for the rest of the program.
      <strong>Whether it makes {budget["target_seconds"] // 60} minutes on the
      real machine is still unmeasured.</strong>
    </p>
    <p class="cap fragment" data-fragment-index="5">
      The cheapest Color Computer of {budget["launch_year"]} had
      {budget["baseline_bytes"]:,} bytes.
      <strong>This would have fitted it</strong>, with
      {budget["baseline_bytes"] - budget["running_bytes"]} to spare, before
      BASIC and the screen take theirs.
    </p>
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
    deck = splice(deck, "ids", figure_identifiers(vocabulary))
    deck = splice(deck, "why", figure_why_three(traces["why_three"]))
    deck = splice(deck, "params", figure_parameters(traces["parameters"]))
    deck = splice(deck, "loop", figure_loop(traces["loop"], traces["budget"], traces["split"]))
    deck = splice(deck, "cost", figure_cost(traces["budget"], traces["split"]))
    DECK.write_text(deck, encoding="utf-8")
    print("spliced 8 figures into presentation/deck/index.html")


if __name__ == "__main__":
    main()
