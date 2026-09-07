# EXP-010: Melody continuation from an audience-entered bar

## Status

**Phase A partially verified.** The model beats the strongest table baseline,
the advantage holds on contexts never seen in training, and the negative
control is clean. On the chosen dance corpus the margin is +0.494 bits.

**Two declared Phase A gates were never measured**, and reporting "Phase A
passed" without saying so was an overstatement:

- every reachable quantized context vector stays within signed 8-bit range;
- the reachable score range fits the declared accumulator width.

Both concern fixed point. Everything measured so far is floating point on a
Mac, and the experiment is for a machine with no floating point at all. Until
those two are checked, the result does not yet say the CoCo can do this — only
that the architecture can.

Phase B, the listening comparison, has not been attempted formally.

Four faults were found and fixed along the way, three of them in the harness
rather than the model. They are recorded under "Phase A result" because each
would have produced a confident wrong answer.

Originally planned. This records the hypothesis, the gates, and the
design before any code is written.

Revised 2026-08-01 from absolute pitches to scale degrees with mode, metre,
beat and chord as context, and split into a progression layer and a melody
layer. The reasoning is in "Why scale degrees" below. Corpus vetting is
recorded under "Corpus"; one leading candidate was disqualified by its own
licence.

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
1 b2 2 b3 3 4 #4 5 b6 6 b7 7    chromatic degrees relative to the tonic
                                 spanning about an octave and a third
HOLD                             the previous note continues
REST                             silence
```

Roughly eighteen output tokens, sized from the measured melodic span rather
than assumed. See the corpus survey for why chromatic degrees rather than
diatonic ones. Duration is expressed as runs of `HOLD` rather than a
separate duration token, keeping one token per row and letting the model learn
note length as part of the same sequence.

Additional context tokens, never predicted:

```text
MAJOR MINOR                       mode, per the corpus survey
I ii iii IV V vi vii              chord under the current row
```

Mode is a separate token rather than folded into the chord, so that what the
model learns about chord V is shared across modes instead of relearned four
times. Degree 3 in major and minor are different intervals, so mode cannot be
left implicit.

Metre and metric position are carried as well. Melody depends strongly on
where it sits in the bar — strong beats take chord tones, weak beats take
passing notes — and with a row-based encoding the model has no other way to
know where the barline is.

```text
4/4 3/4 3/2                       metre, per the corpus survey
BEAT0 .. BEAT7                    position within the bar
```

Context layout, following EXP-008's situational design — the one part of that
experiment that worked:

```text
[ mode, metre, chord, beat, degree(t-k) ... degree(t-1) ]
```

### Two layers, not one

Chords and melody move at different rates and are better modelled separately:

- **A progression model** over chord tokens, one per bar or half-bar. Its
  vocabulary is seven, its sequences are short, and its parameter cost is
  trivial. Bach's harmonic progressions are highly regular, so this is the
  part most likely to be learnable from a modest corpus.
- **A melody model** over degrees, conditioned on the chord the progression
  model produced.

Generation runs the progression first, then the melody within it. This mirrors
how the parts are actually written, keeps each model small enough to gate on
its own evidence, and means a failure can be attributed to one layer rather
than to an entangled whole.

For a first pass the progression may be fixed rather than modelled, so that
the melody model is the only thing under test. Modelling it is the immediate
next step once the melody layer clears its gate.

## Candidate sizes

Each context position carries only the tokens that can appear in it: mode
four rows, metre four, chord seven, beat eight, melody sixteen.
EXP-008 deliberately used a rectangular table and accepted the waste; here the
waste costs roughly half the available context, so the ragged layout earns its
extra complexity.

| Layout | E | Context | History rows | Bars | Parameters |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ragged | 8 | 20 | 16 | 2.7 | 2,376 |
| Ragged | 8 | 28 | 24 | 4.0 | 3,400 |
| Ragged | 8 | 32 | 28 | 4.7 | 3,912 |
| Ragged | 12 | 20 | 16 | 2.7 | 3,556 |
| Rectangular | 8 | 20 | 16 | 2.7 | 4,736 |

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

### Vetting, 2026-08-01

Four candidate sources were examined. **None is unambiguously clean, and one
is disqualified outright.**

| Source | Tunes | Chords | Mode | Metre | Licence | Verdict |
| --- | ---: | --- | --- | --- | --- | --- |
| [The Session](https://thesession.org/) | ~50k settings | no | yes | yes | **Prohibits LLM use** | **Excluded** |
| [Nottingham NMD](https://abc.sourceforge.net/NMD/) | 977 | yes | yes | yes | IPR claimed, no open licence | Risky |
| [Jukedeck cleaned NMD](https://github.com/jukedeck/nottingham-dataset) | ~1000 | yes | yes | yes | GPLv3 on the compilation | Risky |
| [BFDB](https://zenodo.org/records/14692025) | 13,835 | no | no | yes | CC BY-NC 4.0 | Non-commercial, no chords |
| [music21 corpus](https://www.music21.org/music21docs/about/about.html) | 371 chorales | **derivable** | yes | yes | PD music, encodings by permission | Preferred |

**The Session is excluded on its own terms.** Its data licence reads: "You may
not use, adapt, modify, or process the material in any way with Large Language
Models. This includes but is not limited to training Large Language Models."
That is exactly what this experiment would do. The only carve-out is for
accessibility tooling. It is the largest and best-structured corpus of the
four and it cannot be used.

**Nottingham carries a claimed IPR.** The tunes are traditional and long out
of copyright, but the ABC page states the rights in the original collection
"reside with Mick Peat" and no open licence is offered. Bob Sturm additionally
[documented errors introduced by the Jukedeck cleaning](https://highnoongmt.wordpress.com/2018/10/02/going-to-use-the-nottingham-music-database/)
— stripped bass notes and a corrupted repeat structure — and recommends
training on ABC rather than on MIDI conversions.

**BFDB is CC BY-NC.** A conference talk that promotes a consultancy is
arguably a commercial use, and it carries neither chords nor mode.

### Selected: chorale melodies

Bach's chorales are the recommendation, and the reason is not licensing alone.

**The harmony is ground truth, not inference.** Every other candidate would
have required guessing chords from the melody with a heuristic. A four-part
chorale states its harmony explicitly, so the chord token this experiment
conditions on is a fact rather than an estimate. Given that the secondary
hypothesis is precisely about harmonic conditioning, testing it against
guessed chords would have been close to worthless.

**The melodies are themselves traditional.** Bach mostly did not compose these
tunes; he harmonised existing Lutheran hymn melodies, many sixteenth-century
and folk-derived. So this is traditional material with expert harmony attached,
rather than a departure from traditional material.

**Phrase structure is unusually regular** and cadences are unambiguous, which
is exactly the long-range structure the model must capture and a Markov chain
cannot.

Sturm's other finding is directly relevant: models trained on folk data
routinely produce chord progressions that "make no sense", with no
relationship between melody and harmony. Conditioning the melody on a given
chord, rather than generating both jointly, is a deliberate attempt to avoid
that failure mode rather than reproduce it.

The honest cost, again for the stage: **it will sound like a hymn played on a
CoCo.** Slower and more solemn than a dance tune. Whether that is charming or
flat is a judgement to make once something is audible.

### Corpus survey, 2026-08-01

353 chorales are available through music21's iterator, with parts already
named Soprano, Alto, Tenor and Bass, so the melody separates cleanly. Sixty
were sampled, 2,987 melody notes.

| Property | Measured |
| --- | --- |
| Modes | 32 major, 28 minor. No dorian or mixolydian. |
| Metres | 4/4 (54), 3/4 (8), 3/2 (1) |
| Melodic span | median 12 semitones, max 15 |
| Notes outside the diatonic scale | 3.7% |

Three consequences, all of which change the token design.

**Mode needs two tokens, not four.** The corpus is major and minor only.
Metre needs three rather than four.

**One octave, not two.** The median melodic span is exactly an octave and the
widest is 15 semitones. Two octaves of degrees was a guess and it was
generous; the pitch alphabet can be roughly a third smaller, which buys
context depth.

**The 3.7% "out of scale" notes must not be discarded.** Broken down by mode,
they are not noise:

| Mode | Most common alterations |
| --- | --- |
| Minor | raised 6th (37), raised 7th (23), raised 3rd (6) |
| Major | sharpened 4th (19), flattened 7th (18) |

In minor these are the melodic and harmonic minor inflections, and **the
raised 7th is the leading tone** — the note that makes a cadence a cadence.
Discarding it, or snapping it to the natural 7th, would destroy the single
most important structural feature the model is meant to learn. In major the
sharpened 4th marks secondary dominants and the flattened 7th marks
subdominant borrowing; both are ordinary tonal vocabulary.

So melody is represented as **twelve chromatic degrees relative to the tonic**
rather than seven diatonic ones, spanning about an octave and a third.

That gives up "a wrong note is impossible by construction", and the plan
should not pretend otherwise. What replaces it is weaker but honest: 96.3% of
training notes are diatonic, the model sees mode and chord as context, and
**generation can be constrained to in-scale degrees as a sampling policy
rather than as a property of the representation**. Separating the two is the
better design in any case, because it can be tested both ways.

The transposition benefit — every key collapsed onto one tonic — survives
intact, and it was always the larger part of the data-density argument.

### Licence position, checked

music21 itself is BSD. Its corpus carries no blanket grant: "Some encodings
included in the corpus may not be used for commercial uses or have other
restrictions."

- The **Essen folksong collection** bundled with music21 is explicitly
  **non-commercial** and its own licence file states the legal status "is
  unclear". Excluded.
- The **Bach chorales** carry no directory licence file, no embedded rights
  field, and no restriction marker. The music is unambiguously public domain;
  the encodings are Margaret Greentree's, distributed with permission.

The honest statement is that the chorales are the cleanest footing available,
not that an explicit grant exists. Absence of a restriction is not a licence.

### Still to confirm before the corpus is fixed

- Whether 353 chorales yield enough distinct phrases.
- Provenance and licence recorded in `experiments/data/` beside the corpus.
- Holdout must be entirely separate chorales, not held-out phrases.

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

The last two are **not yet measured**. `tools/run_exp_010.py` implements the
first four and prints three of them; the fixed-point gates need the model
quantized first, and that has not been done.

The negative control is not optional. In EXP-008 it caught a harness fault
that made every method appear to score 100%, and later caught
multiple-comparison inflation when the candidate pool grew. Any sweep that
widens the pool must expect the control's limit to trip and select before
scoring rather than after.

## Phase A result

Trained on 281 chorales, evaluated on 57 held-out whole chorales.

| Method | Size | Holdout bits/row |
| --- | ---: | ---: |
| Uniform | — | 4.755 |
| `table/order1` | 29 contexts | 2.621 |
| `table/order1/chord` | 185 | 2.006 |
| `table/order2` | 247 | 1.894 |
| `table/order2/chord` | 1,064 | **1.382** |
| `model/history/H18/E6` | 3,213 params | 1.581 |
| `model/situational/H18/E6` | 3,357 params | **1.140** |

| Gate | Result |
| --- | --- |
| Model beats best table by 0.15 bits | **PASS** (+0.243) |
| Selected candidate within 4,096 parameters | **PASS** (3,357) |
| Negative control within 0.05 bits of unigram | **PASS** (-0.022) |

### The secondary hypothesis is supported, strongly

Situational context beats melody history alone by **0.441 bits** — 1.140
against 1.581 at the same history length and embedding width. Conditioning on
mode, metre, chord and beat is not a refinement here; it is most of the
model's advantage. This is the second time the situational layout from
EXP-008 has been the part that worked.

### The advantage survives on unseen contexts

The claimed mechanism is generalization, so the margin was split by whether
the eighteen-row context had ever appeared in training:

| Bucket | Rows | Model | Table | Margin |
| --- | ---: | ---: | ---: | ---: |
| Seen in training | 2,042 | 1.006 | 1.299 | +0.294 |
| Never seen | 3,772 | 1.212 | 1.427 | +0.215 |

Both methods do worse on novel contexts, as expected. The model keeps most of
its advantage there, which is what the hypothesis required. Note that 65% of
held-out rows have a context never seen in training — the setting the
audience-entered bar will land in is the common case, not the exception.

### What the situational context is actually made of

The four situational tokens were ablated separately, because "situational
context is worth 0.441 bits" says nothing about which part earns it.

| Features | Holdout bits | Cost vs all four |
| --- | ---: | ---: |
| mode + metre + chord + beat | 1.140 | — |
| **chord only** | **1.197** | +0.058 |
| mode + metre + beat | 1.515 | +0.375 |
| beat only | 1.568 | +0.428 |
| mode + metre only | 1.530 | +0.391 |
| history only | 1.581 | +0.441 |

**Chord is nearly the whole of it.** Chord alone comes within 0.058 bits of
all four features together, while everything else combined barely improves on
melody history. Metric position, which was expected to matter because strong
beats take chord tones, is worth 0.013 bits on its own.

This matters beyond bookkeeping: it decides which corpora are usable. A
collection without chord labels cannot supply the feature that is carrying the
result.

### What a chordless corpus would cost

If the corpus has no chords then neither the model nor the tables get them,
so the comparison has to be redone on that footing:

| Method | Contexts / params | Holdout bits |
| --- | ---: | ---: |
| `table/order2` | 247 | 1.894 |
| `table/order3` | 1,058 | 1.714 |
| `model/history/H18/E6` | 3,213 | 1.581 |

The margin falls from **+0.243 to +0.133 bits**, below the declared 0.15 gate.

So chord labels are load-bearing, not decorative. The bundled dance-tune
collections — O'Neill's 2,009 Irish tunes, Aird's 1,180 airs, Ryan's Mammoth
1,059 reels, jigs and hornpipes, all unambiguously public domain by age —
carry no chord symbols, and cannot be used as they stand.

Inferring chords for those collections is far more defensible than it would
have been for chorales: dance-tune harmony is nearly deterministic from the
melody, sitting on I, IV and V with chord tones on strong beats. The important
point is that **both the model and the tables would receive the same inferred
feature**, so the comparison stays fair. What is lost is only the claim that
the harmony is ground truth, and that claim must then be dropped.

## Corpus decision: dance tunes

**Ryan's Mammoth Collection is the corpus**, decided 2026-08-02 on both
measurements and listening. Generated continuations were judged clearly more
melodic than the chorale ones, and the margin over the best table is roughly
double. This is the first decision in the experiment where the numbers and the
ear agreed rather than pointing in different directions.

The chorale pipeline is retained and still runs. It remains the fallback if
inferred chords turn out to be doing something the ground-truth ones would not,
and it is the only corpus where that comparison is possible.

## Dance tunes, with inferred chords

The chordless-corpus problem was solved by inferring the chord rather than
abandoning the corpus. `src/reference/chord_inference.py` scores each diatonic
triad against a bar's notes, weighted by duration and metric position, with a
prior favouring I, IV and V and a mild preference for holding the previous
chord.

That is defensible for dance music and would not have been for chorales.
Reels, jigs and hornpipes sit on I, IV and V with chord tones on the strong
beats; the harmony is close to determined by the melody. Bach's whole interest
is harmony the melody does not imply.

**The chord is now a derived feature, not ground truth, and must be described
that way.** The Phase A comparison stays fair because the model and the table
baselines receive the same derived feature.

376 tunes from Ryan's Mammoth Collection (1883), 70,405 rows, a row to the
sixteenth note because reels are notated in running sixteenths and half the
tune disappears at eighth resolution.

| Method | Params / contexts | Holdout bits | Margin |
| --- | ---: | ---: | ---: |
| `table/order2/chord` | 1,712 | 2.665 | — |
| `model/history` E6 H18 | 4,018 | 2.226 | +0.439 |
| `model/chord` E6 H18 | 4,060 | 2.175 | +0.491 |
| `model/mode+metre+chord+beat` E5 H18 | 3,564 | **2.171** | **+0.494** |

**The margin roughly doubles against chorales**, from +0.243 to +0.494.

### The mechanism is far clearer here

| Bucket | Rows | Model | Table | Margin |
| --- | ---: | ---: | ---: | ---: |
| Seen in training | 878 | 2.670 | 2.542 | **-0.128** |
| Never seen | 11,238 | 2.192 | 2.675 | **+0.483** |

The table wins where it has data. The model wins everywhere else — and
everywhere else is **93% of held-out rows**, against 65% for chorales. Dance
melody is more varied than chorale melody, so contexts repeat less often, so
generalization is worth more. That is the hypothesis stated as plainly as the
data is ever likely to state it.

### Two further faults

**`BEAT_INPUTS` was hardcoded at 12.** At sixteenth resolution a 3/2 or 12/8
bar is 24 rows, so the beat token overflowed its embedding table. It did not
fire earlier because the winning dance configuration used melody history only,
and the configuration that would have used beat was skipped for exceeding the
parameter budget. It is now derived from the widest supported bar.

**The wider pitch range costs context.** Fiddle tunes reach 33 semitones above
the tonic against the chorales' 24, so the melody alphabet grew from 27 tokens
to 34 and the ceiling on history fell with it. The best dance configuration
runs at embedding 5 rather than 6 to stay inside 4,096 parameters.

## Four faults, and what each would have cost

**A corrupted corpus that raised nothing.** `score.chordify()` reflows the
source stream: note offsets stop being absolute and become measure-relative.
Reading them afterwards collapsed a 37-note chorale onto 7 distinct rows. The
extraction completed, reported 341 tunes and 36,676 rows, and produced
melodies that were 76% `HOLD`. Nothing failed; the data was simply wrong. The
melody is now captured in full before `chordify()` is called, and the onset
rate went from 6% to 48%.

**A model declared a failure while still undertrained.** At 10 epochs the
model scores 1.690 bits and loses to the table by 0.276. At 80 it scores 1.140
and wins by 0.243. The first sweep was measuring convergence, not capacity.
EXP-008 diagnosed the same thing, in the opposite direction, and the lesson
did not transfer on its own.

**A negative control with the wrong reference, twice.** First it compared
shuffled-corpus performance against the uniform floor, when shuffling
preserves each tune's token distribution and history legitimately reveals it.
Then, with tokens pooled corpus-wide, it still tripped — because the order-0
baseline was interpolated at 35% empirical against 65% uniform and was not
really a unigram at all.

**A backoff floor that weakened every baseline.** That same interpolation bug
sat underneath all the tables, since they back off through it. Fixing it
strengthened the best table from 1.414 to 1.382 bits and cut the model's
margin from 0.274 to 0.243. The gate is reported against the stronger baseline.

Three of the four were in the measuring apparatus, not the thing being
measured. Each would have produced a confident, wrong, publishable number.

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

## The 6809 core

`make exp010-core` assembles the model and its inference; `make exp010-test`
proves them against the reference.

| | |
| --- | ---: |
| Model data and inference core | 3,985 bytes |
| Alongside the frozen player | 4,973 bytes |
| Multiplies per generated row | 204 |
| Parity criteria | 30, all passing |

The structure follows EXP-007's completion inference with one change: its
context positions all held the same vocabulary, so it stepped between
positional tables by a fixed stride. These do not — mode has two rows, metre
nine, chord seven, beat twenty-four, each melody position thirty-five — so a
table of pointers replaces the stride.

Both hardware bounds were proven unreachable before the assembly was written,
so nothing in it clamps.

### Sampling, not argmax

Argmax is implemented and proven, but generating with it produces a drone:
the most probable row is usually `HOLD`, and always taking it never moves.
The sampler draws in proportion to score.

It needs no division and no 32-bit multiply. Weights come from the same
`exp(-d/32)` table EXP-004 uses, the draw is masked to the smallest power of
two above the running total and retried when it lands past the end, and the
generator is the XorShift16 the Python reference uses, so one seed produces
the same sequence on both machines.

The shift that converts a score drop into a table index sets the temperature.
Measured over the holdout, the drop from the best score has a median of 3,400
and a 99th percentile of 7,705; a shift of four maps that onto the table's
useful range and works out near a softmax temperature of 1.0, which is what
the generated audio was judged at.

Parity covers the weight totals as well as the drawn tokens. The totals pin
the softmax approximation; the tokens pin the draw on top of it.

### A tooling limit worth recording

The direct simulator's assembler crashes, with a Rust `unreachable`, on any
label of sixteen characters or more. A label with nothing after it crashes it
too, which made a bisection lie: every truncated prefix ending at a label
failed regardless of what was actually wrong below, so the search kept
reporting an innocent line.

The fix is the pattern the model experiments already use: assemble with lwasm
and hand the simulator the resulting bytes. That sidesteps the limit and is
the better test anyway, since it exercises the artifact the CoCo would run
rather than a second assembly of the same source.

## What the display caught

The piano roll was built to show generation happening. It also showed a defect
that no measurement in Phase A would have found, because cross-entropy is
computed per row and says nothing about where a tune goes over its length.

Generated tunes started at the bottom of the roll and climbed steadily to the
top without returning. Measured as the change in mean pitch from the first
quarter of a tune to the last:

| | Drift |
| --- | ---: |
| Generated, seed entered at the tonic | +9.5 semitones |
| Real fiddle tunes | +2.1 |
| Generated, seed entered an octave up | **-0.1** |

The cause was the seed, not the model. Extraction places each tune's tonic at
or below its lowest note, so corpus melodies sit a median of fourteen
semitones above the tonic. A figure entered as degree 1 starts at zero — an
octave below anything the model was trained on — and the model responds
exactly as it should, by climbing into the register where its data lives and
staying there.

Entering degrees an octave up puts the figure where the corpus sits, and the
drift disappears.

Two things worth keeping from this. A held-out cross-entropy gate cannot see a
fault that unfolds over a whole tune, so a display is not decoration here; it
is the only instrument that measures shape. And the fault was in the harness,
not the model, which is now the fourth time in this experiment.

## Phase C: entry and performance

A tracker-style keyboard layout for note entry, so a person can play a bar
directly rather than choosing from a menu. Because entry is in scale degrees,
**the keyboard cannot produce an out-of-scale note** — the audience cannot
fumble the seed, and it is guaranteed to be in the same world as the training
data.

The panel title is `YOU SEED - MODEL CONTINUES`. The entered figure is also
labelled `SEED` and drawn in yellow while the continuation is green, so human
and model authorship remains legible in words, position, and colour.

The generated tune is written into the frozen row format and handed to the
EXP-009 player. Bass, arpeggio and percussion come from fixed rules keyed to
the chord progression.

The player must not be modified. If generation needs something the row format
cannot express, that is a finding to record, not a licence to unfreeze a
component that took two rounds of timing work to get right.

## The sampler's floor (2026-08-03)

Reported by ear: the melody sounded "a little too random". Measured with
`tools/measure_melody_randomness.py`, over sixty generated tunes against the
holdout, on the things that make a line sound random - notes outside the
mode, mean absolute interval, and intervals wider than a fifth.

| | out-of-scale | mean step | leaps | floor mass |
| --- | --- | --- | --- | --- |
| Real fiddle tunes (holdout) | 1.9% | 2.97 | 5.5% | - |
| shift 4, floor 1 (as shipped) | 5.5% | 3.84 | 10.4% | 3.5% |
| shift 4, floor 0 | 3.8% | 3.33 | 6.6% | 0% |
| shift 3, floor 0 | 3.0% | 2.52 | 1.2% | 0% |
| shift 2, floor 0 | 3.1% | 2.04 | 0.1% | 0% |

`EXP_LUT` floored every weight at 1 so that no token would be impossible.
With thirty-four tokens that is 3.5% of each draw spent uniformly over the
whole vocabulary, and because it is uniform it lands on chromatic notes and
wide leaps far more often than the model would. The floor was removed; the
temperature was not touched.

Sharpening the temperature was the obvious alternative and the measurement
rejects it. At a shift of 3 leaps fall to 1.2% against the corpus's own 5.5%

- the generations become *more* regular than real fiddle tunes, which is a
different failure with the same cause: a sampler that has stopped listening
to the model. The corpus is the target, not a floor to beat.

What remains is the model's own error, not the sampler's: 3.8% out-of-scale
against 1.9%, and a mean step of 3.33 against 2.97. Both say the generations
are still a little more active than the real thing.

## The fixed progression is atypical, and it is not the problem (2026-08-03)

`demo_prog` is `I I IV V`, one bar of eight rows each. It exists because the
model consumes a chord per row as context and does not produce one: at
training time the chords came from each tune's own melody via
`chord_inference.py`, and at generation time there is no melody yet to infer
from. It also feeds the arranger's bass root and arpeggio.

Measured against the corpus, it is representative in its vocabulary and
wrong in its motion:

| | corpus | demo_prog |
| --- | --- | --- |
| share of rows on I, IV, V | 95.5% | 100% |
| rows per chord | median 16, mean 21.3 | 8 |
| `IV -> V` share of changes | 5.2% | 33% |

Corpus changes are dominated by motion to and from the tonic: `I->V` 20.9%,
`V->I` 20.6%, `I->IV` 17.0%, `IV->I` 15.7%, together 74% of all changes.
`I I IV V` spends a third of its changes on `IV->V`, which the corpus barely
uses.

It was then tested as a cause of the generations' excess activity, and it is
not one. Holding the sampler fixed and varying the progression - slowing it
to sixteen rows, reshaping it to alternate with the tonic, `I V I V` -
changes nothing measurable:

| progression | rows/chord | out-of-scale | mean step | leaps |
| --- | --- | --- | --- | --- |
| I I IV V | 8 | 3.8% | 3.33 | 6.6% |
| I I IV V | 16 | 4.0% | 3.33 | 6.6% |
| I V I IV | 16 | 3.8% | 3.33 | 6.4% |
| I IV I V | 16 | 3.9% | 3.34 | 6.8% |
| I V I V | 16 | 3.7% | 3.36 | 6.9% |

All within noise of each other, none near the corpus's 1.9 / 2.97 / 5.5. So
the progression's shape is worth fixing for its own sake if a listener wants
it more idiomatic, but it does not explain why the generations move more
than real tunes do. That remains open.

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
7. The generations remain more active than the corpus (3.8% out-of-scale
   against 1.9%) with the sampler now honest. Undertraining or the
   fixed-point quantisation are still open. The fixed chord progression is
   not - see below.

## Addendum, 2026-09-06: the performer is now the steady clock

The demo's performer was EXP-009's player, and on the CoCo 3 through the
1703 its row-change stall was audible as a warble on the melody voice.
EXP-018, the steady sample clock, removed it, and the demo now performs
through that player: `src/6809/steady_player.asm` with
`src/6809/steady_compile.asm`, which turns the composed rows into the
player's event stream on the CoCo, cursor writes included, so the
playback cursor is drawn by the stream rather than by a hook between
samples. The compiler mirrors the reference's line for line and
`make exp010-compile-test` proves it on 128 rows: the same 12,037 bytes.

Two builds: `build/coco-melody-demo.bin` for the CoCo 1 at 4,566 Hz, and
`build/coco-melody-demo-6309.bin` for a CoCo 3 with a 6309, whose
performer runs in native mode at the fast clock, 11,188 Hz. The composer
and the display are the same code in both; only the player and the tune
frame's increments differ. `make block9-6309` is the stage launch for the
second, beside `make block9`. `make melody-dsk` puts both on the SDC's
names, `MELODY09.BIN` and `MELODY39.BIN`, and on `MELODY10.DSK`. Both
compose, compile and play to the end under XRoar with all-ones RAM
(`make exp010-xroar-test`), through `demo_run`, the keyboard-free entry.

The move found a fault. The row buffer sat at `$2C00` and its last 194
bytes lay on top of the model's position tables at `$3200`, so the first
performance composed correctly and every later one composed from a
corrupted model; the direct-simulator parity test composes before it
arranges and could not see it. The layout is packed lower now with room
between regions, and the compiled stream has the 14 KiB from `$4800` to
the top of a 32 KiB machine. A dense tune at seven ticks a row compiles
to about 12 KiB; if the buffer ever fills, the compiler stops emitting,
sets `compile_overflow`, and the tune ends early rather than overwriting
anything.

What changed for the listener: no warble, and on the CoCo 1 a fifth less
sample rate. The trade was heard and preferred on the CoCo 3 in EXP-018.
On the CoCo 1 it has not been heard yet.
