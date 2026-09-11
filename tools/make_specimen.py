#!/usr/bin/env python3
"""Render the palette and type specimen for the browser deck.

This page exists to be looked at. The project has been caught twice reasoning
about a display from its documentation and getting it wrong, so the palette,
the font and the screen geometry all get put on a page and inspected rather
than trusted.

It also doubles as the deck's own smoke test: if Hot CoCo stops loading or a
role colour goes missing, this is where it shows.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
OUT = ROOT / "presentation" / "specimen.html"
PALETTE = ROOT / "presentation" / "coco-palette.json"

# Semigraphics-4 in the Private Use Area: one codepoint per VDG cell byte,
# E080 + (byte - 0x80). $8F lights all four quadrants, so U+E08F is a solid
# block. The font supplies the shape; CSS supplies the colour.
BLOCK = ""

# The result marks from the game opponent, in the order a session produced them.
MARKS = ["win", "loss", "tie", "win", "win", "loss", "win"]

ROWS = [
    "1 ROCK   2 SPOCK  3 PAPER",
    "4 LIZARD 5 SCISSORS",
    "",
    "YOU WIN 42%",
    "",
    None,  # the marks row, built with colour spans
    "YOU  ROC PAP SPO LIZ ROC SCI",
    "CPU  SCI ROC PAP SPO LIZ PAP",
    "",
    "PAPER COVERS ROCK",
    "YOU LOSE - IT THREW PAPER",
    "",
    "IT EXPECTS SCISSORS",
    "RULES  19/25",
    "MEMORY 47/47",
]
TITLE = "RPSLS - IT LEARNS AS YOU PLAY"
COLS = 32


def marks_row() -> str:
    cells = "".join(f'<span class="coco-block {m}">{BLOCK}</span> ' for m in MARKS)
    pad = " " * (COLS - 2 * len(MARKS) - 1)
    return "  " + cells.rstrip() + pad


def main() -> None:
    data = json.loads(PALETTE.read_text())
    composite, roles = data["composite"], data["roles"]

    swatches = "".join(
        f'<div class="sw"><span class="chip" style="background:{c}"></span>'
        f'<span class="lab">{i:02d}<br>{c}</span></div>'
        for i, c in enumerate(composite)
    )
    role_chips = "".join(
        f'<div class="sw"><span class="chip" style="background:{v["hex"]}"></span>'
        f'<span class="lab">{k}<br>c{v["index"]:02d}</span></div>'
        for k, v in roles.items()
    )
    samples = "".join(
        f'<p class="spec" style="font-size:{s}px">THE QUICK BROWN FOX 0123456789 '
        f"!?&amp;*()#$%&lt;&gt;=+-/</p>"
        for s in (14, 20, 28, 40)
    )
    blocks = "".join(
        f'<span class="coco-block {n}">{BLOCK}</span>' for n in ("win", "tie", "loss")
    )
    body = "\n".join(marks_row() if r is None else r.ljust(COLS)[:COLS] for r in ROWS)

    OUT.write_text(
        f"""<!doctype html>
<meta charset="utf-8">
<title>CoCo palette and type specimen</title>
<link rel="stylesheet" href="coco-palette.css">
<link rel="stylesheet" href="coco-type.css">
<style>
  body {{ margin:0; padding:24px; background:#111; color:#eee;
         font:14px/1.5 system-ui,sans-serif; }}
  h1 {{ font-size:18px; margin:0 0 4px; }}
  h2 {{ font-size:13px; text-transform:uppercase; letter-spacing:.08em;
        color:#999; margin:28px 0 10px; font-weight:600; }}
  .grid {{ display:grid; grid-template-columns:repeat(16,1fr); gap:4px; }}
  .grid.roles {{ grid-template-columns:repeat(12,1fr); }}
  .sw {{ text-align:center; }}
  .chip {{ display:block; height:38px; border-radius:2px; }}
  .lab {{ display:block; font:9px/1.25 ui-monospace,monospace; color:#888;
          margin-top:3px; }}
  .screen {{ font-size:24px; display:inline-block; }}
  .spec {{ font-family:var(--coco-type); color:var(--coco-bg); margin:6px 0; }}
  .big {{ font-size:44px; letter-spacing:6px; }}
  .note {{ color:#888; max-width:62ch; }}
</style>
<h1>CoCo palette and type specimen</h1>
<p class="note">Composite palette, transcribed from the reference table and
checked hex against decimal. Hot CoCo, served as shipped.</p>

<h2>Composite palette</h2>
<div class="grid">{swatches}</div>

<h2>Roles</h2>
<div class="grid roles">{role_chips}</div>

<h2>Hot CoCo at size</h2>
{samples}

<h2>Semigraphics blocks, U+E08F coloured by CSS</h2>
<p class="big">{blocks}</p>

<h2>A screen, 32 by 16</h2>
<div class="coco-screen screen"><span class="bar">{TITLE.center(COLS)}</span>
{body}</div>
""",
        encoding="utf-8",
    )
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
