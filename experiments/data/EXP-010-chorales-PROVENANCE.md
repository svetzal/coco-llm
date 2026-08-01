# EXP-010 corpus provenance

## What this is

`EXP-010-chorales.jsonl` holds 341 Bach chorales reduced to the EXP-009
player's row grid. One JSON object per chorale, one token per row.

Regenerate with:

```sh
make exp010-corpus
```

## Source

J. S. Bach's four-part chorales, as distributed in the corpus bundled with
[music21](https://www.music21.org/), reached through
`music21.corpus.chorales.Iterator(numberingSystem='bwv')`.

## Rights

**The music is public domain.** Bach died in 1750.

**The encodings** are Margaret Greentree's edited collection, distributed with
music21 by permission.

music21 itself is BSD licensed. Its corpus carries **no blanket grant**; the
corpus licence states that "Some encodings included in the corpus may not be
used for commercial uses or have other restrictions: please see the licenses
embedded in individual compositions or directories for more details."

Checked on 2026-08-01:

- the `bach/` directory contains no licence file;
- the chorale files contain no `rights` or copyright field;
- no restriction marker applies to them.

The honest position is that this is **the cleanest footing available, not an
explicit grant**. Absence of a restriction is not a licence. If the talk is
recorded or published commercially, this is worth a second look.

The **Essen folksong collection** also bundled with music21 was examined and
**excluded**: its licence file states the legal status "is unclear" and grants
non-commercial use only.

[The Session](https://thesession.org/) was examined and **excluded outright**.
Its data licence reads: "You may not use, adapt, modify, or process the
material in any way with Large Language Models. This includes but is not
limited to training Large Language Models." It was the largest and
best-structured candidate.

## Encoding

Produced by `tools/extract_chorales.py` against `src/reference/melody_tokens.py`.

| Field | Meaning |
| --- | --- |
| `melody` | one token per row: pitch as semitones above the tonic, or HOLD, or REST |
| `chords` | chord root as a scale degree, zero-based, read from the four-part harmony |
| `beats` | position within the bar |
| `mode` | `major` or `minor` |
| `metre` | `4/4`, `3/4` or `3/2` |
| `tonic` | the key's tonic, recorded so the encoding can be reversed |
| `split` | `train` or `holdout`; every sixth chorale is held out as a whole tune |

A row is an eighth note. The harmony is read from the alto, tenor and bass
rather than inferred from the melody, which matters because the experiment's
secondary hypothesis is about harmonic conditioning.

## Extraction results, 2026-08-01

| | |
| --- | ---: |
| Chorales considered | 353 |
| Extracted | 341 |
| Rows | 36,676 |
| Train / holdout tunes | 284 / 57 |

Rejected, with reasons:

| Count | Reason |
| ---: | --- |
| 4 | changes metre mid-tune |
| 4 | no harmony at the first row |
| 2 | melody leaves the pitch range |
| 1 | metre 12/8, outside the supported set |
| 1 | no melody notes |

Nothing is silently dropped: every rejection is counted and reported by the
extraction tool.

## Two traps recorded

**`Key.getScale()` returns the key signature's scale.** For G minor it hands
back B flat major, so every minor chorale would be encoded a third out — and
the result would look entirely plausible. The scale is built from the key's
own tonic and mode instead.

**Melodic span is not the same as range above the tonic.** The measured
melodic span is a median of one octave, but a melody can still reach 24
semitones above the tonic, because the tonic may sit up to eleven semitones
below the lowest note the melody uses. A pitch ceiling set from the span alone
rejected 15% of the corpus.
