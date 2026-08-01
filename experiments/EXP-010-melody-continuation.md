# EXP-010: Melody continuation from an audience-entered bar

## Status

Planned. No implementation. This records the hypothesis, the gates, and the
design before any code is written.

Revised 2026-08-01 from absolute pitches to scale degrees with a mode token
and chord-conditioned context. The reasoning is in "Why scale degrees" below,
and it changed the experiment materially rather than cosmetically.

## Question

Can a stock CoCo 1 take a bar of melody entered by a person, continue it into
a tune that sounds like it belongs to the same phrase, and play the result on
the EXP-009 player — using a model small enough to sit alongside the player in
32 KiB?

## Why the prompted form matters

The audience enters the opening bar; the CoCo composes the rest and performs
it. That is a better demonstration than unprompted generation for a reason
beyond showmanship: **the audience already knows what they played, so they can
judge whether the continuation belongs to it.** Nobody has to take the result
on trust.

It is also the setting where the model's one real advantage is exercised
hardest. A bar entered by a person is very likely to be a context no n-gram
table in the training corpus has ever seen. A sparse table has nothing to say
and must back off; embeddings place unseen contexts near similar seen ones. If
the model cannot win here, it cannot win anywhere.

## Why scale degrees

The first draft of this experiment used absolute pitches: two chromatic
octaves, 26 tokens. Under that scheme the model has to infer which seven of
twelve semitones are currently in play, from context alone, with no hidden
layer. That is a conjunctive inference — "these pitches belong together
*because* the key is G minor" — and an additive model that sums independent
per-position contributions is poorly suited to it. The expected failure is
occasional out-of-key notes, which read as broken rather than as interesting.

Representing melody as scale degrees makes that failure impossible by
construction, and buys two further things.

**Context depth.** At the same parameter ceiling, a smaller vocabulary reaches
further back:

| Representation | Vocab | Model context | Table context |
| --- | ---: | ---: | ---: |
| Chromatic, 2 octaves | 26 | 18 rows, 3 bars | 2 |
| Scale degrees, 2 octaves | 16 | 30 rows, 5 bars | 3 |

Five bars against three is the difference between seeing a phrase and seeing a
fragment of one. Phrase shape is exactly what a Markov chain cannot produce
and what would make the output sound composed rather than wandering.

**Data density.** Sixteen tokens spreads a modest corpus less thinly than
twenty-six, which matters when the corpus is a few hundred melodies rather
than a few million.

### The cost, which belongs on stage

Constraining to a scale means **the harmony is handed to the model, not
learned by it.** What remains to be learned is contour, phrase length, rhythm
through `HOLD` runs, repetition, and cadence. That is still a substantial
task, and the decision is the same category as tokenizing language into words
rather than characters. But the honest framing is "it cannot play a wrong note
because it was never given one", not "it learned harmony."

This experiment must not let an audience believe otherwise.

## Hypothesis

An additive fixed-point model of no more than 4,096 parameters, trained on
public-domain folk and classical melodies represented as scale degrees, will
predict held-out melody rows with lower cross-entropy than order-2 and order-3
frequency tables of comparable size, and will continue an arbitrary
human-entered bar into eight bars that a listener judges to belong to the same
phrase.

A secondary hypothesis concerns conditioning. Carrying the current chord and
mode as context positions will outperform melody history alone, because
voice-leading depends on harmonic function rather than on note statistics.

## Null result to respect

Markov-chain melody generation is a well-known technique that produces
plausible music, and an order-3 table over sixteen tokens is 4,096 contexts —
it fits. If a table matches the model within the declared margin, the honest
conclusion is that the model is not earning its multiplier, exactly as in
EXP-008.

The screening test from that experiment applies in full:

| Criterion | Verdict |
| --- | --- |
| Context space too large to tabulate | Passes. 16^30 is not a number to tabulate. |
| Real structure to generalize across | Passes. Phrasing, cadence, contour. |
| No cheap algorithm at least as good | **At risk.** This is the gate. |

## Token design

The EXP-009 player is frozen, so its row format is the target: one cell per
row per channel, 6 ticks per row, about 8.3 rows per second.

Predicted tokens, one per row:

```text
1 2 3 4 5 6 7        scale degrees, lower octave
1' 2' 3' 4' 5' 6' 7' scale degrees, upper octave
HOLD                 the previous note continues through this row
REST                 silence
```

Sixteen output tokens. Duration is expressed as runs of `HOLD` rather than a
separate duration token, keeping one token per row and letting the model learn
note length as part of the same sequence.

Additional context tokens, never predicted:

```text
MAJOR MINOR DORIAN MIXOLYDIAN     mode
I ii iii IV V vi vii              chord under the current row
```

Mode is a separate token rather than folded into the chord, so that what the
model learns about chord V is shared across modes instead of relearned four
times. Degree 3 in major and minor are different intervals, so mode cannot be
left implicit.

Context layout, following EXP-008's situational design — the one part of that
experiment that worked:

```text
[ mode, chord, degree(t-k) ... degree(t-1) ]
```

## Candidate sizes

Each context position carries only the tokens that can appear in it: mode
positions need four rows, chord positions seven, melody positions sixteen.
EXP-008 deliberately used a rectangular table and accepted the waste; here the
waste costs roughly half the available context, so the ragged layout earns its
extra complexity.

| Layout | E | Context | History rows | Bars | Parameters |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ragged | 8 | 18 | 16 | 2.7 | 2,280 |
| Ragged | 8 | 24 | 22 | 3.7 | 3,048 |
| Ragged | 8 | 32 | 30 | 5.0 | 4,072 |
| Ragged | 12 | 18 | 16 | 2.7 | 3,412 |
| Rectangular | 8 | 18 | 16 | 2.7 | 4,032 |

Context length is **not declared here**. Phase A sweeps it, because the ragged
layout is a real complication for a later 6809 port and should only be paid
for if the extra context measurably helps. Selecting the smallest candidate
within one percentage point of the best follows EXP-007's rule.

Generation costs 16 x E multiplies per note — 128 at E=8, about 5 ms. A 64-row
tune composes in under half a second.

That composing and playing cannot overlap is a constraint, not a choice:
EXP-009 established that playback consumes the whole machine. The CoCo
composes into RAM, then performs.

## Corpus

Public-domain folk and classical melodies. Chosen over chiptune sources
because licensing must be clean for a recorded public talk, and because folk
melody has strong, short, repeating phrase structure — the long-range
regularity the model needs in order to beat a short-context table.

The cost is honest and should be stated on stage: it will sound like folk
music played on a CoCo, not like a 1985 game soundtrack.

Requirements the corpus must meet:

- machine-readable melody, monophonic or with a clear melody line;
- chord labels, or a defensible way to infer them, since chord is a context
  token and also drives the accompaniment channels by rule;
- an identifiable mode per tune;
- provenance and licence recorded in `experiments/data/` beside the corpus;
- holdout melodies that are entirely separate tunes, not held-out phrases from
  training tunes.

ABC-notation folk collections are the leading candidate because they are
largely traditional material and frequently carry chord symbols already.

Every melody is transposed so that its tonic is degree 1. Whether that helps
by removing a nuisance variable or destroys something worth learning is an
open question below, and is cheap to test both ways.

## Baselines

Order-2 and order-3 frequency tables with backoff, as in EXP-008, where making
the table strong is what makes the comparison mean anything.

The memory argument, stated precisely. Storing only the most likely next token
per context:

| Method | Contexts | Bytes | Fits beside the player? |
| --- | ---: | ---: | --- |
| Order-2 table | 256 | 256 | Yes |
| Order-3 table | 4,096 | 4,096 | Yes |
| Order-4 table | 65,536 | 65,536 | No |
| Model, 30 rows of context | — | 4,072 | Yes |

The claim is not that the model is smaller than any table. It is that the
model reaches thirty rows of context at a size where tables reach three.

## Phase A gates: Mac reference

Proceed to 6809 work only if all hold:

- the model's held-out cross-entropy is at least 0.15 bits per row below the
  best table baseline;
- the advantage is larger on contexts absent from the training corpus than on
  contexts present in it, since that is the mechanism being claimed;
- chord-and-mode conditioning beats melody history alone, or the secondary
  hypothesis is recorded as unsupported and the simpler layout is used;
- the model does not beat a uniform baseline on a shuffled corpus;
- the selected candidate fits 4,096 parameters;
- every reachable quantized context vector stays within signed 8-bit range;
- the reachable score range fits the declared accumulator width.

The negative control is not optional. In EXP-008 it caught a harness fault
that made every method appear to score 100%, and later caught
multiple-comparison inflation when the candidate pool grew. Any sweep that
widens the pool must expect the control's limit to trip and select before
scoring rather than after.

## Phase B gates: continuation quality

Cross-entropy measures prediction. This experiment claims something else, so
it needs its own acceptance test.

- Given twenty human-entered opening bars, the model continues each into eight
  bars.
- Continuations are compared blind against the best table baseline on the same
  seeds.
- A listener judges which continuation belongs to its opening bar.

If the model wins on cross-entropy but loses the listening comparison, that is
reported as it stands. Better prediction does not guarantee better generation:
a model that hedges toward the most probable row can score well and still
produce something dull.

## Phase C: entry and performance

A tracker-style keyboard layout for note entry, so a person can play a bar
directly rather than choosing from a menu. Because entry is in scale degrees,
**the keyboard cannot produce an out-of-scale note** — the audience cannot
fumble the seed, and it is guaranteed to be in the same world as the training
data.

The generated tune is written into the frozen row format and handed to the
EXP-009 player. Bass, arpeggio and percussion come from fixed rules keyed to
the chord progression.

The player must not be modified. If generation needs something the row format
cannot express, that is a finding to record, not a licence to unfreeze a
component that took two rounds of timing work to get right.

## Open questions

1. Does transposing every melody to a common tonic help by removing a nuisance
   variable, or destroy something worth learning? Cheap to test both ways.
2. Is one token per row the right resolution, or does it waste vocabulary on
   `HOLD` runs that a note-plus-duration encoding would capture better?
3. Should the entered bar be ordinary context, or should generation be biased
   to return to its pitches, as a human continuing a phrase would?
4. Two octaves of degrees is assumed sufficient. Does the corpus fit after
   transposition, or do folk melodies need more range?
5. Should the chord progression itself be modelled, rather than fixed? It is a
   short sequence over seven tokens and would be a very small second model.
6. Does the ragged embedding layout earn its complexity, or is rectangular at
   shorter context good enough to keep the 6809 port simple?
