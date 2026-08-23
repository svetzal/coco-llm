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


def figure_shift(shift: dict) -> str:
    """What the eight shift instructions do to the bits, one pair at a time."""
    rows = []
    for n, step in enumerate(shift["steps"]):
        bits = step["bits"]
        cells = "".join(
            f'<span class="bit{" on" if b == "1" else ""}'
            f'{" edge" if i == 7 else ""}">{b}</span>'
            for i, b in enumerate(bits)
        )
        dropped = (
            ""
            if step["dropped"] is None
            else f'<span class="fell">{step["dropped"]}</span>'
        )
        label = "gradient" if n == 0 else f"asra rorb &times;{n}"
        rows.append(
            f'<div class="brow2{" last" if n == len(shift["steps"]) - 1 else ""}'
            f' fragment" data-fragment-index="{n}">'
            f'<span class="blab2">{label}</span>'
            f'<span class="bits">{cells}</span>'
            f'<span class="bfell">{dropped}</span>'
            f'<span class="bdec">{step["value"]}</span>'
            f'<span class="breal">{step["real"]:+.4f}</span></div>'
        )

    first, last = shift["steps"][0], shift["steps"][-1]
    return f"""
  <div class="fig shifts">
    <div class="bhead">
      <span class="blab2"></span>
      <span class="bits"><span class="half">A &mdash; asra</span>
        <span class="half">B &mdash; rorb</span></span>
      <span class="bfell">out</span>
      <span class="bdec">int</span>
      <span class="breal">value</span>
    </div>
    {"".join(rows)}
    <p class="cap fragment" data-fragment-index="{len(shift["steps"])}">
      Q4.12: the integer is the real value times {shift["scale"]}.
      <code>asra</code> drops A's low bit into the carry and
      <code>rorb</code> rotates it into the top of B, so the pair shifts all
      sixteen bits at once. <strong>{first["value"]} becomes
      {last["value"]}.</strong> The next instruction subtracts it from the
      weight, which is why the One Step slide shows that change as
      {-last["real"]:+.4f}.
    </p>
  </div>"""


def figure_sign(fix: dict) -> str:
    """Why one subtraction turns an unsigned product into a signed one."""

    def word(value: int, cls: str = "") -> str:
        bits = format(value, "016b")
        cells = "".join(
            f'<span class="bit{" on" if b == "1" else ""}'
            f'{" edge" if i == 7 else ""}">{b}</span>'
            for i, b in enumerate(bits)
        )
        return f'<span class="bits {cls}">{cells}</span>'

    return f"""
  <div class="fig shifts sign">
    <div class="brow2">
      <span class="blab2">the factor</span>
      <span class="plain">{fix["factor"]}</span>
      <span class="bexpl">MUL cannot take a negative, so it arrives as
        {fix["unsigned_factor"]}, which is 256 too big</span>
    </div>
    <div class="brow2 fragment" data-fragment-index="1">
      <span class="blab2">two MULs give</span>
      {word(fix["raw"])}
      <span class="bexpl">{fix["unsigned_factor"]} &times;
        {fix["multiplier"]} = {fix["raw"]}, and wrong</span>
    </div>
    <div class="brow2 fragment" data-fragment-index="2">
      <span class="blab2">too big by</span>
      <span class="plain">256 &times; {fix["multiplier"]}</span>
      <span class="bexpl">which in the low word is just
        {fix["excess_high"]}, sitting in the high byte</span>
    </div>
    <div class="brow2 fragment last" data-fragment-index="3">
      <span class="blab2">suba 1,x</span>
      {word(fix["corrected"])}
      <span class="bexpl">= {fix["signed"]}, and
        {fix["factor"]} &times; {fix["multiplier"]} =
        {fix["factor"] * fix["multiplier"]}</span>
    </div>
    <p class="cap fragment" data-fragment-index="4">
      Compare the two bit rows: <strong>the low byte is identical.</strong>
      Only the high half moved, because that is where the whole error was.
      Five instructions is the difference between this machine being able to
      train a model and not.
    </p>
  </div>"""


def figure_code(excerpt: dict, note: str) -> str:
    """One assembly reveal, taken verbatim from the source that assembles."""
    lines = "".join(
        f'<div class="cline{" hot" if line["hot"] else ""}">'
        f'{esc(line["text"])}</div>'
        for line in excerpt["lines"]
    )
    elided = (
        '<div class="cline elide">...</div>' if excerpt["begins_inside"] else ""
    )
    tail = '<div class="cline elide">...</div>' if excerpt["dropped_comments"] else ""
    return f"""
  <p class="lead">{esc(excerpt["title"])}</p>
  <div class="fig code">
    <pre class="asm">{elided}{lines}{tail}</pre>
    <p class="cap">{note} <span class="src">{esc(excerpt["source"])}</span></p>
  </div>"""


# One colour per maker, so the same maker is the same colour in every bar.
MAKER_CLASS = {"APPLE": "mk-a", "COMMODORE": "mk-c", "TANDY": "mk-t"}


def figure_bias(trace: dict) -> str:
    """Same everything, different data. Then same data, different order."""

    def row(run: dict, index: int, note: str = "") -> str:
        # Segments label themselves, so the figure needs no legend and the
        # reader never has to hold a colour mapping in their head.
        def label(maker: str, count: int) -> str:
            if count >= 3:
                return f"{maker} {count}"
            return str(count) if count >= 2 else ""

        segments = "".join(
            f'<span class="seg {MAKER_CLASS[maker]}" '
            f'style="width:{100 * run["counts"][maker] / run["total"]:.1f}%">'
            f'{label(maker, run["counts"][maker])}</span>'
            for maker in trace["makers"]
        )
        if run["other"]:
            segments += (
                f'<span class="seg mk-o" '
                f'style="width:{100 * run["other"] / run["total"]:.1f}%"></span>'
            )
        return (
            f'<div class="brun fragment" data-fragment-index="{index}">'
            f'<span class="blab">{esc(run["label"].lower())}</span>'
            f'<span class="bbar">{segments}</span>'
            f'<span class="bsample">{esc(run["sample"])}</span>'
            f'<span class="bnote2">{note}</span></div>'
        )

    fans = "".join(row(run, n + 1) for n, run in enumerate(trace["runs"][:3]))
    concatenated, interleaved = trace["runs"][3], trace["runs"][4]

    return f"""
  <div class="fig bias">
    <p class="lbl">one collection each</p>
    {fans}
    <p class="lbl fragment" data-fragment-index="4">
      the same {concatenated["names"]} names, balanced, in two orders
    </p>
    {row(concatenated, 4, "end to end")}
    {row(interleaved, 5, "shuffled together")}
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
        re.S,
    )
    if not pattern.search(source):
        raise SystemExit(f"no marker region for figure {name!r} in the deck")
    return pattern.sub(lambda m: f"{m.group(1)}{body}\n  {m.group(2)}", source)


def main() -> None:
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
        "note": "Not one number in the model moved between those four "
        "answers. <strong>A prompt is not training. It is the first few "
        "tokens of the answer, handed over before the machine starts.</strong>",
    }

    # Block 5. Values are the ones the EXP-011 build puts on screen; the
    # locked-model line is verbatim from attention_ui.asm.
    context_change = {
        "held": [
            "model 751B, weights locked",
            "the question, asked again word for word",
            "all eight context records but one",
        ],
        "pairs": [
            ("context says", "LISA = CODE 2", "LISA = CODE 6"),
            ("we asked", "LISA?", "LISA?"),
            ("it answered", "CODE 2", "CODE 6"),
        ],
        "note": "A person typed one digit into context RAM and the answer "
        "changed. <strong>MODEL 751B DID NOT CHANGE.</strong> Training "
        "changes weights; prompting changes context; attention uses context "
        "to produce this answer.",
    }
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
    deck = splice(deck, "bias", figure_bias(bias))
    deck = splice(deck, "promptchange", figure_changed(prompt_change))
    deck = splice(deck, "contextchange", figure_changed(context_change))
    deck = splice(deck, "twomuls", figure_code(
        code["two_muls"],
        "The 6809 multiplies two unsigned bytes. This makes a signed multiply "
        "out of two of them, and it is running right now.",
    ))
    deck = splice(deck, "signfix", figure_code(
        code["sign_fix"],
        "A negative factor comes out 256 too large. One subtraction fixes it, "
        "and the model is bit-for-bit what it was before.",
    ))
    deck = splice(deck, "signbits", figure_sign(traces["sign_fix"]))
    deck = splice(deck, "shiftbits", figure_shift(traces["shift"]))
    deck = splice(deck, "lrcode", figure_code(
        code["learning_rate"],
        "Shift right four times and you have divided by sixteen. That is the "
        "learning rate: not a setting, an instruction count.",
    ))
    DECK.write_text(deck, encoding="utf-8")
    print("spliced 16 figures into presentation/deck/index.html")


if __name__ == "__main__":
    main()
