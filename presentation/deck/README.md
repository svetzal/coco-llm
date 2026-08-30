# Deck

The talk, as a reveal.js deck. Nine blocks matching
[`../runsheet.md`](../runsheet.md) block for block.

Open it. There is no build step:

```sh
open presentation/deck/index.html
```

Press `S` for the speaker view. It carries the presenter notes and paces
against the runsheet's budget, because each `<section>` sets `data-timing` to
its block's minutes in seconds and `totalTime` is the forty minutes of content.
Every slide's notes open with a block marker — `BLOCK 3 OF 9 - ON THE
MACHINE - SLIDE 2/7` — and every block has a matching command, `make block1`
through `make block9`, which prints the block's cues and launches its
emulator where one is involved.

Notes are HTML, because the speaker view renders the aside's markup and
plain text collapses into a wall. The conventions: one `<p>` per thought,
its text on one source line so the view wraps it naturally; `<ul><li>` for
key maps and launch lists; the block marker's `<p>` wrapped in `<strong>`;
and a literal `<` in note text written as `&lt;` — a bare `<END>` parses as
a tag and silently vanishes from the speaker window.
If the speaker view says you are behind, that is the runsheet's cut order
becoming relevant: block 6 goes first, then block 5's demo shortens to its
slide, block 3 shortens rather than goes, block 8 never goes.

Blocks 3, 4, 5, 6 and 8 run in XRoar rather than here. Their slides carry the
`cue` class and stay nearly empty so the projector is not competing with the
emulator window. Each cue opens with `.call`: the block's falsifiable
hypothesis, stated before the window switch, so the demo is a shot the room
watched being called. Blocks 6 and 8 close with an explainer slide that
lands the lesson after the demo.

## Why it looks like this

The deck wears the machine's own body: black ink on the composite screen
green, with the CoCo's reversed title bar — green on black — pinned to the
top of every slide as chrome. Projectors want a bright field, which the old
green-on-black deck did not give them, and the deck and the machine now
speak one visual language: what the room sees on a slide is what the room
sees on the CoCo's screens, bar and all.

Each of the runsheet's nine blocks owns a palette colour, worn as a thin
band under the title bar on every slide and as the full background of the
chapter card that opens the block. The bar text and band come from
`data-bar` and `data-block` attributes on each `<section>`; a new slide
copies its neighbours'. The cards carry only a number, the block title, and
the arc word — the spoken segue lives in their notes, not on the wall.

Emphasis is deep red on the green field. The old deck's cue — a slide and
an XRoar window being colour-inverses of each other — is retired; the title
bar now does that wayfinding job by name.

## Writing slides

- Colours come from `../coco-palette.css`. Never write a hex value in a slide
  or in the theme.
- Type comes from `../coco-type.css`. Hot CoCo is the deck face and the code
  face, so an assembly excerpt and the screen it produces share one alphabet.
- **Everything in Hot CoCo is folded to uppercase.** The MC6847 has no
  lowercase, and Hot CoCo is faithful about it: lowercase maps to the character
  ROM's inverse forms, so a lowercase letter renders as a filled block with the
  letter knocked out. Sentence-case text comes out reversed. The theme folds it
  up for you.
- To get that inverse effect on purpose, add `class="inv"`. It lowercases the
  text, which is not a trick: it is how the character ROM is addressed.
- `.prose` and `.what` use a real sans and keep their own case. Reach for
  `.prose` rarely. If a slide needs a paragraph it is usually two slides.
- `.screen` renders a block of text as the machine would, black on green, with
  `.bar` for a reversed title row.
- Semigraphics blocks are `U+E08F` with `class="coco-block win|tie|loss"`. A
  font cannot carry colour, so the glyph gives the shape and CSS gives the
  colour.

## Figures

Diagrams live in marked regions of `index.html`:

```html
<!-- FIGURE:step -->  ...generated...  <!-- /FIGURE:step -->
```

Everything outside the markers is hand-edited. Everything inside is generated,
and will be overwritten:

```sh
uv run python tools/export_deck_traces.py   # run the model, write the numbers
uv run python tools/make_deck_figures.py    # draw them, splice them in
```

**Every number in a figure comes from a real run.** The copy discipline says no
sample output goes on a slide unless the machine produced it, and a figure is
sample output. So `data/traces.json` is exported from the reference model:
the 29 token identifiers, the three-number context vector, all 29
probabilities, and the weights that move when the model is corrected. Nothing
is rounded into a tidier shape. When someone in the front row asks whether
those are the real numbers, the answer is yes.

That also means a figure cannot drift away from the model. Change the model,
re-export, and the slide changes with it.

**Animation is reveal fragments and no JavaScript.** Where a figure has a
before and an after, the after is drawn on top of the before as a fragment.
Stepping forward replaces one with the other, and stepping back undoes it,
which a scripted animation usually will not. Order is controlled with
`data-fragment-index` so a figure's stages advance in the order the argument
needs rather than in document order.

**One vocabulary, and it is the audience's.** The deck names the terms people
arrive already having heard, and uses them consistently: **token** and
**tokenizing**, **context window**, **parameter**, **embedding**. Internal
words are a tell that a figure was written from the code rather than for a
reader, so "slot" became "window position" everywhere once the context window
had a name. If a figure needs a word the audience has not been given, give it
the word first.

The speaker notes extend the same move to words the material earns but the
slides do not need: **hallucination** and **overfitting** on the epochs
slide, **inference**, **open weights** and **the P in GPT** on the cost
slide, **temperature** against greedy decoding in block 4, **system prompts,
RAG and memory** as context edits in block 5, **fine-tuning** as more
upbringing in block 7, and long chats forgetting their start as the window
sliding. The rule for adding one: the mechanism must already be on screen,
so the word lands on something visible rather than replacing it.

**Nothing in a figure may shrink.** Every box carries `flex: 0 0 auto`.
Flex items shrink below their own content by default, and a bordered box
holding a number is exactly where that shows: the border cuts through the
digits, and the figure quietly displays a value that is not the value. If a row
does not fit, the row is wrong. Split it rather than letting it squeeze.

Two related rules that came out of the same bug: a stage label must not be
wider than the boxes it names, because `.lbl` is `nowrap` and will happily
overrun its neighbours; and a figure with more than three stages in a row will
not fit a 1280 slide at a size the back row can read.

**A fetched value needs a visible source.** Showing a row pulled out of a
table, without the table, makes the row look conjured. The lookup slide exists
because the step figure asserted three numbers and could not say where they
came from.

**Caption with `.cap`, not `.lbl`.** `.lbl` is sized in `em` and scoped inside
`.fig`, so it compounds with any figure that scales itself down to fit; the
lookup tables run at `0.4em` and an em-sized caption there came out at 8px.
`.cap` is sized in px, which is stable because reveal scales the whole 1280
canvas.

**Three text roles, and they are not interchangeable.** `.lead` is a sentence
under a heading that frames the figure below it. `.cap` annotates a figure from
inside it and is px-sized so it survives a figure scaling itself down. `.lbl`
names one part within a figure and is em-sized. Using `.cap` outside a `.fig`
silently renders it at heading size, which is how the lookup caption first went
wrong.

To inspect a figure with every stage showing at once, open it with fragments
off:

```sh
open "presentation/deck/index.html?fragments=false#/2"
```

## Vendored

`vendor/reveal/` holds reveal.js 6.0.1, MIT, with its `LICENSE`. It is checked
in rather than installed so the deck opens from a file with no toolchain and no
network. A conference room is the wrong place to discover a missing dependency.
Only the parts in use were extracted: the core, the notes plugin, and the
highlight plugin.

## Regenerating

Three steps, in order. The middle one depends on the assembled 6809 build, so
`make coco-bin` has to have run:

```sh
uv run python tools/export_deck_traces.py      # run the model, write the numbers
uv run python tools/measure_train_vs_infer.py  # classify the image by job
uv run python tools/export_bias_trace.py       # the five controlled bias runs
uv run python tools/export_shift_trace.py      # a real weight update, bit by bit
uv run python tools/export_prompt_trace.py     # prompted completions and the baseline
uv run python tools/extract_code_excerpts.py   # pull assembly from the source
uv run python tools/make_deck_figures.py       # draw them all, splice them in
```

`extract_code_excerpts.py` reads the assembly reveals out of `src/6809/` by
label rather than letting them be retyped, matches highlights by instruction
rather than line number, and refuses to emit an excerpt outside the five-to-
twelve-line limit `learning-journey.md` sets. A slide of code that has gone
stale is worse than no slide of code.

`measure_train_vs_infer.py` splits the assembled image into what is needed to
**learn** a model, what is needed to **use** one, what both phases share, and
what only the self-check needs. It attributes every byte by symbol and refuses
to run if any symbol is unclassified, so a new routine cannot quietly land in
the wrong bucket. The classification is a judgement about each routine's job
and lives in one table at the top of that file.
