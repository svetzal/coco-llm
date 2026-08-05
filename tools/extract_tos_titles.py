#!/usr/bin/env python3
"""Pull every Star Trek: The Original Series episode title from Wikipedia.

The titles are the corpus for EXP-012. They are a good fit for a CoCo-sized
model: a closed, finite set with a strong shared grammar ("The <noun> of
<noun>"), written by a small number of people over three years, so a model
can plausibly learn the shape without needing to learn English.

Wikipedia keeps the list page and the three season pages separately - the list
page transcludes the season tables rather than containing them, so scraping it
alone yields two titles and looks like it worked. Each season page is fetched
directly.

Uppercase is not a stylistic choice. The CoCo's text screen has no lowercase,
so the machine's vocabulary is the uppercase one, and counting anything else
would count words the target cannot display.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parents[1]
DEFAULT_OUTPUT = ROOT / "experiments" / "data" / "EXP-012-tos-titles.txt"

RAW = "https://en.wikipedia.org/w/index.php?title={}&action=raw"
AGENT = "coco-llm-research/1.0 (https://github.com/svetzal; talk corpus)"

# "The Cage" was made first and aired last, twenty-four years later. It is
# listed on the index page rather than in any season, so it is named here.
PILOT = "The Cage"
PAGES = [
    ("Star Trek: The Original Series season 1", 29),
    ("Star Trek: The Original Series season 2", 26),
    ("Star Trek: The Original Series season 3", 24),
]
# Season 1 airs 29 episodes but lists 28 titles: "The Menagerie" is one title
# over two parts. A count mismatch anywhere else means the page changed shape.
TWO_PART = {"The Menagerie"}

TITLE_LINE = re.compile(r"^\|Title=(.*)$")

# The CoCo's character set is ASCII. "Operation - Annihilate!" is written with
# an en dash and "Mudd's Women" with a typographic apostrophe; both are folded
# to what the machine can actually print, and anything left over is an error
# rather than a silent substitution.
ASCII_FOLD = {"–": "-", "—": "-", "‘": "'", "’": "'", "“": '"', "”": '"', "…": "..."}


def fetch(page: str) -> str:
    url = RAW.format(urllib.parse.quote(page.replace(" ", "_")))
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def unwiki(raw: str) -> str:
    """Wikitext to the title as it is written."""
    raw = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", raw)  # [[target|shown]]
    raw = re.sub(r"\[\[([^\]]*)\]\]", r"\1", raw)
    raw = raw.replace("''", "")  # italics: the ''Enterprise'' Incident
    raw = re.sub(r"<[^>]+>", "", raw)
    raw = raw.replace("&nbsp;", " ")
    for fancy, plain in ASCII_FOLD.items():
        raw = raw.replace(fancy, plain)
    return " ".join(raw.split())


def titles_of(wikitext: str) -> list[str]:
    return [
        unwiki(match.group(1))
        for match in (TITLE_LINE.match(line) for line in wikitext.splitlines())
        if match
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--cache",
        type=Path,
        help="directory of previously downloaded wikitext, to work offline",
    )
    arguments = parser.parse_args()

    collected = [PILOT]
    for page, episodes in PAGES:
        if arguments.cache:
            wikitext = (arguments.cache / f"{page}.wiki").read_text(encoding="utf-8")
        else:
            wikitext = fetch(page)
        found = titles_of(wikitext)
        expected = episodes - sum(1 for title in found if title in TWO_PART)
        if len(found) != expected:
            raise SystemExit(
                f"{page}: expected {expected} titles for {episodes} episodes, "
                f"found {len(found)}. The page layout has changed."
            )
        collected += found

    duplicates = [t for t in collected if collected.count(t) > 1]
    if duplicates:
        raise SystemExit(f"duplicate titles: {sorted(set(duplicates))}")

    text = "\n".join(title.upper() for title in collected) + "\n"
    unprintable = sorted({c for c in text if not (32 <= ord(c) < 127 or c == "\n")})
    if unprintable:
        raise SystemExit(f"not printable on a CoCo: {unprintable}")

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(text, encoding="ascii")

    words = sum(len(title.split()) for title in collected)
    print(f"{len(collected)} titles, {words} words -> {arguments.output}")
    print("(78 aired titles over 79 episodes, plus the unaired pilot)", file=sys.stderr)


if __name__ == "__main__":
    main()
