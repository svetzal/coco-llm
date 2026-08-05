# EXP-012 corpus provenance

## What this is

`EXP-012-tos-titles.txt` holds every *Star Trek: The Original Series* episode
title, one per line, uppercased and folded to ASCII.

79 lines: the 78 distinct titles aired over the series' 79 episodes, plus the
unaired first pilot "The Cage". The two counts differ because "The Menagerie"
is a single title spanning two episodes.

Regenerate with:

```sh
make exp012-corpus
```

## Source

The English Wikipedia season articles, fetched as raw wikitext:

- `Star Trek: The Original Series season 1` (28 titles, 29 episodes)
- `Star Trek: The Original Series season 2` (26)
- `Star Trek: The Original Series season 3` (24)

Retrieved 2026-08-04.

**Not** `List of Star Trek: The Original Series episodes`. That page
*transcludes* the season tables rather than containing them, so an extractor
pointed at it returns two titles — the pilots — and gives every appearance of
having worked. `tools/extract_tos_titles.py` fetches each season page directly
and fails loudly if a page's title count stops matching its episode count.

## Rights

**The titles are facts about a television series**, not creative expression
taken from Wikipedia. A list of episode names in broadcast order carries no
original authorship of its own — Wikipedia is the route to the data, not the
author of it — so the CC BY-SA licence on Wikipedia's prose does not attach to
this file. Wikipedia's own contributions here are the article text, which is
not reproduced.

**The titles are the property of the rights holder** (CBS Studios / Paramount).
Naming a television episode in order to discuss, index, or build a
demonstration around it is ordinary referential use. This corpus is 259 words of
episode names; it contains no dialogue, no plot text, no script material, and
no artwork.

The honest position: **fine for a conference talk and for the repository, and
worth a second look before anything commercial**, on the trademark question
rather than the copyright one. Star Trek is an actively enforced mark, and a
product that generated Star Trek-styled names would be a different proposition
from a talk that demonstrates a 1981 computer doing so.

This is a weaker constraint than EXP-010 faced. No source consulted here
carries a term forbidding use with language models, which was the reason The
Session was excluded from the music corpus.

## Encoding

Produced by `tools/extract_tos_titles.py`.

One title per line, uppercase ASCII, no other markup. Uppercase is not
stylistic: the CoCo's text screen has no lowercase, so the machine's vocabulary
is the uppercase one and counting any other would count words it cannot show.

Two ASCII folds were required, and the extractor rejects the run if any
character survives that a CoCo could not print:

| Written | Stored | Where |
| --- | --- | --- |
| en dash `–` | `-` | "Operation – Annihilate!" |
| apostrophe `’` | `'` | "Mudd's Women", "Friday's Child", "Spock's Brain", "Plato's Stepchildren" |

Italics are stripped: "The *Enterprise* Incident" becomes `THE ENTERPRISE
INCIDENT`.

## Measurements, 2026-08-04

| | |
| --- | ---: |
| Titles | 79 |
| Word tokens | 259 |
| Vocabulary | 180 tokens (179 words + boundary) |
| Words used exactly once | 162 |
| Distinct bigrams | 174 of 180 |

Full analysis in
[`../EXP-012-episode-titles.md`](../EXP-012-episode-titles.md). The short
version: only `OF THE` and `IN THE` ever repeat, so there is almost no
repeated evidence for a next-word model to learn from.
