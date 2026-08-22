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
If the speaker view says you are behind, that is the runsheet's cut order
becoming relevant: block 6 goes first, then block 4, block 3 shortens rather
than goes, block 8 never goes.

Blocks 3, 4, 5, 6 and 8 run in XRoar rather than here. Their slides carry the
`cue` class and stay nearly empty so the projector is not competing with the
emulator window.

## Why it looks like this

The machine draws its body black on green and reverses to green on black for a
title bar. The deck takes the reversed one, which is also what a dark room
wants. The machine keeps black on green.

So cutting from a slide to XRoar inverts the screen. That is the point: the
audience can tell who is talking without being told.

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

## Vendored

`vendor/reveal/` holds reveal.js 6.0.1, MIT, with its `LICENSE`. It is checked
in rather than installed so the deck opens from a file with no toolchain and no
network. A conference room is the wrong place to discover a missing dependency.
Only the parts in use were extracted: the core, the notes plugin, and the
highlight plugin.
