# Posts

Drafts of the blog series, in the order of [`../series-outline.md`](../series-outline.md).
Each post's frontmatter follows the blog's own; `published: false` until it
moves to the blog repository.

## Figures

Figures are SVG, drawn in the deck's own palette and type: black ink on the
composite screen green, the reversed title bar in Hot CoCo, block 2's amber
for the thing that changed. The SVG is the source; the PNG beside it is what
the post references.

Render with headless Chrome, which honours an `@font-face` pointing at the
deck's font file and installs nothing. `rsvg-convert` will not do: on macOS it
takes the system font list and Hot CoCo falls back to Helvetica.

```sh
S=$(mktemp -d)
{ printf '<!doctype html><meta charset="utf-8"><style>@font-face{font-family:"Hot CoCo";src:url("file://%s/presentation/fonts/HotCoCo.ttf")}html,body{margin:0}</style>' "$PWD"; cat presentation/posts/images/two-words-at-a-time.svg; } > "$S/fig.html"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars \
  --window-size=1536,980 --force-device-scale-factor=1 --screenshot="$S/fig.png" "file://$S/fig.html"
cp "$S/fig.png" presentation/posts/images/two-words-at-a-time.png
```

Every figure ends with two full-canvas overlays, a faint scanline pattern and a
radial darkening at the corners, so the drawn figures and the generated
illustrations read as the same screen.

Everything in Hot CoCo is uppercase, because the MC6847 has no lowercase and
the font renders lowercase as inverse-video blocks. Small explanatory labels
use a real sans, uppercase and letterspaced, as the deck's chapter cards do.
