# EXP-002: Token model feasibility

**Status:** integer reference supported; physical hardware pending

## Context

EXP-001 showed that character-level training spends too much of the CoCo 1
budget evaluating forty possible characters for every character in a
729-example corpus.

Contemporary language models do not normally treat individual characters as
tokens. This experiment uses complete name components as a deliberately simple
tokenizer. `COMMODORE AMIGA` becomes two tokens rather than sixteen characters.

## Question

Can a tiny token-level model learn enough structure from a curated corpus to
generate recognizable, novel computer names within the CoCo 1 time budget?

## Hypothesis

An additive model with:

- 29 tokens, including an end marker;
- a two-token context;
- three-value, position-dependent embeddings;
- a full 29-token softmax;
- 290 trainable parameters;

will produce a majority of name-like, novel samples after twenty epochs.

The run will require 302,760 matrix multiplications. That leaves sufficient
budget to implement fixed-point sign handling, lookup-based softmax, memory
access, and display updates within three minutes on a 0.89 MHz 6809E.

## Name-like rubric

Write the rubric before running the fixed sample:

- the generated name contains two to four tokens;
- its first token is a manufacturer that begins at least one training name;
- every output token comes from the visible 29-token vocabulary.

Novel means the complete generated name does not occur in the training corpus.
This rubric measures recognizable structure, not factual correctness or
subjective quality.

## Procedure

1. Train from deterministic seed 6809 for twenty epochs.
2. Use online SGD with learning rate 1/16.
3. Generate twenty samples at temperature 0.7.
4. Record loss, checksum, novelty, and name-like rate.
5. Replace floating-point operations with bit-exact fixed-point operations.
6. Port and measure the critical 6809 kernels.
7. Measure the complete run on physical CoCo 1 hardware.

## Evidence

The deterministic floating-point run used twenty epochs, learning rate 1/16,
temperature 0.7, and seed 6809.

| Measure | Result |
| --- | ---: |
| Vocabulary | 29 tokens |
| Parameters | 290 |
| Training examples | 58 |
| Initial loss | 3.3683 |
| Final loss | 1.8478 |
| Matrix multiplications | 302,760 |
| Name-like samples | 20 of 20 |
| Novel samples | 19 of 20 |
| Checksum prefix | `d119918f2f4b8f0e` |

Representative generated samples:

```text
SINCLAIR AMIGA
TANDY ARCHIMEDES
COMMODORE TRS-80
TANDY MODEL COMPUTER
TANDY 128
```

One sample, `SINCLAIR ZX81`, reproduced a training name. The other nineteen
combined learned tokens into names absent from the corpus.

The integer-only run uses:

- signed Q4.12 master parameters;
- signed Q4.4 forward operands from each master's high byte;
- Q8.8 logits;
- probabilities and output errors in units of 1/256;
- a 256-entry exponential lookup table;
- a learning rate of 1/16 implemented through shifts;
- deterministic 16-bit xorshift initialization and sampling.

After twenty epochs, loss fell from 3.5588 to 1.8687. Fifteen of twenty samples
met the predeclared name-like rubric and seventeen were novel. Representative
integer-generated names included:

```text
TANDY COMPUTER
COMMODORE ST
TANDY PET
COMMODORE LISA
TANDY MACINTOSH
```

Its checksum prefix was `5ee491db953d0ce7`.

## Conclusion

The floating-point and integer references support the quality and
operation-count portions of the hypothesis. Fixed-point loss is close to the
floating-point result, although unconstrained fixed-point sampling produces
more malformed names. That visible limitation is acceptable for the exhibit and
must not be hidden by silently filtering output.

Tokenization is now the leading architecture because it simultaneously improves
audience comprehension and reduces training work. The experiment remains open
until the integer test vectors run through the 6809 implementation and a
complete training run is measured on the physical CoCo 1.

## Appended evidence: was twenty epochs the right place to stop?

Twenty was chosen in the hypothesis above and never tested. Building the
presentation raised the obvious objection: if the model keeps improving, why
not train longer and get names that read better?

`tools/sweep_epoch_quality.py` answers it. At each point in a 120-epoch run it
draws 200 samples and scores them on two axes: novel, and name-like by the
rubric written above before any sample was seen.

| Epochs | Loss | New | Like a name | Both |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 3.368 | 100% | 0% | 0% |
| 5 | 2.424 | 98% | 54% | 52% |
| 10 | 2.072 | 94% | 91% | 84% |
| 13 | 1.959 | 95% | 97% | 92% |
| **15** | 1.898 | 94% | 98% | **93%** |
| 20 | 1.786 | 91% | 98% | 90% |
| 30 | 1.598 | 74% | 100% | 74% |
| 40 | 1.421 | 55% | 99% | 55% |
| 60 | 1.164 | 28% | 99% | 28% |
| 120 | 0.957 | 2% | 99% | 1% |

Neither axis alone is the quantity of interest. Novelty by itself rewards the
untrained model, which invents constantly and never produces a name.
Name-likeness by itself peaks when the model recites the corpus, because real
names are trivially name-like. Only both at once measures the behaviour the
demonstration needs.

Three findings:

- **The objection is wrong, and instructively so.** Name-likeness saturates at
  98% by epoch 13 and never improves. Training past twenty cannot make the
  output more recognizable, because it is already as recognizable as it gets.
  What further training buys is recitation: by epoch 60 the model returns a
  corpus name 72% of the time, and by epoch 120 almost always.
- **Twenty is inside the plateau but is not its peak.** The useful band runs
  from about 13 to 25 epochs, peaking at 15 with 93% against twenty's 90%. The
  difference is small and twenty remains a defensible choice; it is also the
  number the 6809 build has baked in as `TRAIN_EPOCHS`, so the deck and the
  machine agree.
- **Loss keeps falling the whole way** — 3.368 down to 0.957 — while the
  behaviour we care about rises, plateaus, and then collapses. This is the
  same result as the EXP-007 epoch sweep, reproduced on a model 28 times
  smaller, and it is the clearest evidence in the project that the optimizer's
  number is not the goal.

### What the rubric cannot see

The name-like test is two checks: the sample has two to four tokens, and its
first token is one of the six makers that start a real name (ACORN, APPLE,
ATARI, COMMODORE, SINCLAIR, TANDY). Nothing else. `TANDY TANDY TANDY` passes
it, and so does `APPLE 400 400`.

That is a measure of structure, not of quality, and it should not be quoted as
though it were the latter. Two things keep it usable. It was written before any
sample was seen, so it could not be adjusted to fit a result. And the
degenerate cases are rare where the number is being used: of the 197 samples
that pass at twenty epochs, 3 repeat a token. At five epochs 14 of 109 do, so
the early figures are the inflated ones.

A stronger rubric would reject repeated tokens outright. It has deliberately
not been changed, because rewriting a rubric after seeing the results is how
a measurement stops being evidence.

Nothing above changes the hypothesis or the recorded twenty-epoch run. It
records that the choice was checked afterwards and survived.
