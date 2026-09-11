#!/usr/bin/env python3
"""Export the dealt title screen for the deck's figures.

The deck may only show titles the machine actually deals, so this records the
sixteen rows of the demo screen — the same deterministic build the titles
parity test pins to the CoCo binary — into the deck's data directory. Run it
under the project venv (the reference model needs numpy):

    .venv/bin/python tools/export_titles_trace.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from make_titles_parity_test import expected_screen

OUT = ROOT / "presentation" / "deck" / "data" / "titles.json"


def main() -> None:
    _, titles = expected_screen()
    dealt = [title for title in titles if title]
    OUT.write_text(json.dumps({"dealt": dealt}, indent=2) + "\n", encoding="utf-8")
    print(f"exported {len(dealt)} dealt titles to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
