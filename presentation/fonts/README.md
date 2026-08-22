# Fonts

## Hot CoCo

`HotCoCo.ttf` is the deck's typeface, and the deck's code font. It is Rebecca
G. Bettencourt's TrueType rendering of the MC6847 character generator, which is
the chip that drew every character a CoCo 1 ever put on a screen. Assembly
excerpts on a slide and the screen they produce therefore share one alphabet,
which is the reason to use it rather than a nostalgic-looking substitute.

Copyright Kreative Korporation / Kreative Software. Obtained from
<https://www.kreativekorp.com/software/fonts/trs80.shtml>.

### Licence

Kreative Software Relay Fonts Free Use License version 1.2f. The full text is
in [`FreeLicense.txt`](FreeLicense.txt), which is part of the distribution and
must travel with the font files.

It permits use, display, embedding, and redistribution. Three conditions bind
this project:

1. **No selling.** Copies may not be sold for a fee.
2. **Licence and credit travel with it.** Any copy given away includes this
   licence verbatim and credits Kreative Korporation or Kreative Software.
   Deleting `FreeLicense.txt` breaks the licence.
3. **No modification and no derivative works.**

Condition 3 is the one that constrains the build. **Serve the `.ttf` as it
arrived.** Do not subset it, do not convert it to WOFF2, do not run it through
a font pipeline. A format re-encode is arguably a derivative work, the file is
80 KB, and that is cheaper than the argument. `coco-type.css` loads it directly
for this reason.

Note that the general terms on the KreativeKorp website are narrower than this.
The licence shipped inside the archive is the one that governs these files, and
it is more permissive. Stacey has also written to ask directly, so if a reply
narrows any of the above, this file is where the answer goes.

### Variants

| File | Character set |
| --- | --- |
| `HotCoCo.ttf` | MC6847, the CoCo 1 and 2. **The one the deck uses.** |
| `HotCoCo2Y.ttf` | Same, double height. |
| `HotCoCoWithT.ttf` | MC6847T1, the CoCo 3, adding lowercase. |
| `HotCoCoWithT2Y.ttf` | Same, double height. |

### Codepoints

The character set sits in the Private Use Area rather than at ASCII, so plain
text renders through the font's own Latin-1 glyphs and the authentic VDG forms
are reached deliberately:

- `U+E000-U+E07F` the MC6847 character set, one codepoint per character byte.
- `U+E080-U+E0FF` Semigraphics 4, one codepoint per cell byte `$80-$FF`. The
  cell byte is `1 C C C L L L L`, so `$8F` lights all four quadrants and
  `U+E08F` is a solid block. A font cannot carry colour: the glyph gives the
  shape and CSS gives the colour, which is how the game opponent's win, tie and
  loss marks are drawn on a slide.
- `U+E100-U+E1FF` Semigraphics 6.

Every glyph advances 800 units in a 1200-unit em, which is the VDG's 8 by 12
pixel cell exactly. The screen geometry in `coco-type.css` follows from that
measurement rather than from taste.
