# EXP-007: All-RAM sentence completion

## Status

Runnable in XRoar. The expanded punctuated corpus, deterministic model,
all-RAM 6809 inference core, punctuation-aware workbench, and emulator checks
exist. Physical CoCo 1 loading and stock-rate latency evidence remain
outstanding.

## Question

Can a 64 KiB CoCo 1 use an all-RAM memory map to run a substantially larger,
punctuation-aware completion model that produces short sentences while
remaining responsive enough for an interactive demonstration?

## Hypothesis

A 255-token additive fixed-point model with five tokens of context will make the
completion workbench materially more expressive than EXP-006. A 48 KiB weight
ceiling will permit the experiment to compare 32, 40, and 48 KiB candidates
without assuming that filling all available memory improves quality.

The smallest candidate whose expanded-corpus quality is within one percentage
point of the best candidate on both top-three accuracy and keystroke savings
will be preferred.

## Why this is a separate experiment

EXP-006 remains the frozen 8 KiB milestone: 178 tokens, four-token context,
nine embedding dimensions, and a model ending at `$7FFF`. EXP-007 changes four
material constraints:

1. It uses the CoCo 1's all-RAM memory mode.
2. It raises the model ceiling to 48 KiB.
3. It tokenizes `. , ? ! : ;` separately so generation can form sentences.
4. It increases context from four tokens to five.

The punctuation tokens consume context positions. Five-token context therefore
preserves roughly the same recent-word visibility near a sentence boundary
that EXP-006 had without punctuation.

## Candidate architecture

The additive model has one signed value per parameter:

```text
parameters = V × (E × (C + 1) + 1)
```

where `V` is vocabulary size, `C` is context length, and `E` is embedding
width. Keeping token identifiers to one byte caps the complete vocabulary,
including `<END>`, at 255 tokens.

For `V=255` and `C=5`:

| Ceiling | Embedding | Parameters | Padding | Scoring multiplies |
| ---: | ---: | ---: | ---: | ---: |
| 32 KiB | 21 | 32,385 | 383 | 5,355 |
| 40 KiB | 26 | 40,035 | 925 | 6,630 |
| 48 KiB | 31 | 47,685 | 1,467 | 7,905 |

Six punctuation tokens plus `<END>` leave room for 248 word tokens, 71 more
than EXP-006.

## Memory-map candidate

The Motorola MC6883/SN74LS783 SAM provides a Type 1 map intended for RAM-based
systems. The [MC6883 data sheet](https://maltedmedia.com/6809/Sheets/Data/MC6883.pdf)
and the
[Tandy Color Computer Technical Reference Manual](https://support.retrorewind.ca/media/coco/color_computer_technical_reference_manual_tandy_.pdf)
are the primary references for the implementation.

A contiguous 48 KiB working model fits exactly at:

```text
$3F00-$FEFF  49,152 model bytes
$FF00-$FFFF  CoCo I/O and SAM control; never model storage
```

The current EXP-006 resident image ends below `$2E00`. EXP-007 must keep its
program, vocabulary strings, UI state, and a relocated stack below `$3F00`.
This must be enforced by assembly symbols rather than assumed.

Entering all-RAM mode hides the BASIC ROM used by the current `POLCAT` keyboard
call. The loader and UI must therefore prove one of these strategies:

- briefly restore the ROM map around keyboard polling, then return to all-RAM;
- replace `POLCAT` with a small keyboard scanner; or
- use a loader/runtime interface supplied by CoCo SDC or FujiNet.

Loading bytes beneath the normal ROM window is a separate acceptance test.
DECB starts in SAM Type 0, where an address above `$7FFF` selects a 32 KiB RAM
page rather than contiguous high RAM. A loader that writes the final model
directly at `$8000` therefore wraps and corrupts the display and resident
program.

The runnable design quantizes each parameter to a signed Q2.2 nibble and packs
two parameters per byte. Its 16,193-byte transport image loads below `$8000`
with the resident program. Startup masks interrupts, selects Type 1, and
expands the nibbles to signed bytes at `$8000-$FE80`. Masking matters because
Type 1 also exposes RAM over the ROM interrupt vectors; an interrupt during
unpacking would otherwise jump through uninitialized RAM.

## Punctuation tokenization

EXP-007 introduces a separate reference tokenizer. It uppercases input, keeps
words and numbers intact, and emits `. , ? ! : ;` as individual tokens.
Unsupported characters fail visibly rather than disappearing.

The 6809 workbench will need matching behaviour:

- accept the punctuation keys supported by the CoCo keyboard;
- parse punctuation without requiring a visible leading space;
- render punctuation against the preceding word;
- include punctuation in the five-token context; and
- preserve prefix completion for word tokens.

EXP-006's space-delimited parser remains unchanged.

## Workbench UI reuse

EXP-007 will reuse EXP-006's complete ten-row editor and cursor-anchored,
edge-corrected suggestion popover. The shared UI is deliberately unaware of
experiment vocabulary, context size, model layout, and keyboard hardware.

Each experiment supplies narrow policy hooks for initialization, keyboard
input, accepted typed characters, prediction, and suggestion insertion.
EXP-007's policy will:

- display `255 TOKENS / 5 TOKEN CONTEXT` on the bottom row;
- accept the selected punctuation characters as input;
- tokenize punctuation independently from words;
- attach punctuation without a leading space while retaining normal spacing
  between words;
- present `<END>` as a ranked stop option instead of silently displaying the
  next lexical token;
- call the expanded EXP-007 scorer; and
- read the keyboard safely while BASIC ROM is hidden by the all-RAM map.

This preserves the presentation lesson: the audience sees the same practical
completion tool grow a larger vocabulary and context, while the assembly files
make the parts special to sentence completion easy to identify.

## Phase A: frozen-corpus capacity sweep

Run:

```sh
make exp007-sweep
```

This first sweep deliberately reuses EXP-006's 147 training phrases and
24 holdout phrases. It isolates memory, context, and embedding width before
the vocabulary and task change.

| Budget | Context | Embedding | Top one | Top three | Saved | Max magnitude |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 32 KiB | 4 | 36 | 42.6% | 60.2% | 61.9% | 66 |
| 32 KiB | 5 | 30 | 40.7% | 57.4% | 61.6% | 83 |
| 32 KiB | 6 | 26 | 41.7% | 60.2% | 61.2% | 103 |
| 40 KiB | 4 | 45 | 43.5% | 59.3% | 60.8% | 61 |
| 40 KiB | 5 | 38 | 41.7% | 59.3% | 61.4% | 76 |
| 40 KiB | 6 | 32 | 39.8% | 59.3% | 61.4% | 81 |
| 48 KiB | 4 | 55 | 41.7% | 59.3% | 61.6% | 61 |
| 48 KiB | 5 | 45 | 41.7% | 57.4% | 59.7% | 66 |
| 48 KiB | 6 | 39 | 39.8% | 60.2% | 59.7% | 82 |

All listed candidates keep every possible quantized context vector within a
signed byte. Increasing memory or context does not improve the frozen task.
This rejects “use all 48 KiB because it is available” as a design rule.

Five-token context remains the EXP-007 hypothesis because the new sentence
task includes punctuation and longer dependencies. It must earn that choice
on the new corpus.

## Phase B gates

The expanded experiment proceeds to 6809 assembly only if:

- the complete vocabulary is no larger than 255 tokens;
- its broader holdout has a lower unknown-token rate than EXP-006;
- top-three accuracy is at least EXP-006's recorded 59.3%;
- keystroke savings is at least 60%;
- the chosen fixed-point quantization retains useful top-three accuracy;
- every possible context vector remains in signed 8-bit range;
- the chosen model fits its declared 32, 40, or 48 KiB image; and
- stock-rate CoCo 1 latency is measured and explicitly accepted.

## Phase B baseline evidence

The runnable candidate uses:

| Measurement | Result |
| --- | ---: |
| Training sentences | 150 |
| Holdout sentences | 31 |
| Vocabulary | 243 tokens |
| Context | 5 tokens |
| Embedding width | 22 |
| Parameters | 32,319 |
| Quantization | Signed Q2.2 |
| Scoring multiplies | 5,346 |
| Holdout top one | 50.8% |
| Holdout top three | 63.5% |
| Holdout keystroke savings | 54.2% |
| Packed transport image | 16,160 bytes |
| Expanded working model | 32,319 bytes |
| All-context magnitude | 28 |
| Proven score range | -1,579 to 1,725 |

The 32 KiB model satisfies the vocabulary, top-three, quantization, context,
score-width, and memory gates. It does not satisfy the declared 60% keystroke
savings gate. That miss remains part of the result; the runnable artifact is a
demonstration candidate, not evidence that the original hypothesis is fully
supported.

The DECB image contains resident code and the packed model below `$7F00`.
Startup expands the working model at `$8000-$FE3E`. XRoar with 64 KiB RAM and
the verified Tandy ROMs reaches the editor after the complete load, map switch,
and unpack path. The keyboard adapter briefly restores both the ROM map and its
interrupt environment for `POLCAT`, then masks interrupts before exposing the
model again. Direct-simulator tests prove bit-exact top-three ranking,
five-token parsing, punctuation attachment, visible `<END>` rendering, and
stop-token acceptance.

This was the first runnable corpus. It is retained as baseline evidence rather
than rewritten after the experiment changed.

## Expanded conversational corpus

The present runnable model broadens the lesson from isolated slogans and
commands to short questions, answers, explanations, and alternate sentence
shapes. It keeps the retro-computing setting while varying brands, hardware,
actions, and claims. The holdout is separate, contains no duplicate training
sentence, and uses only vocabulary learned from training.

| Measurement | Result |
| --- | ---: |
| Training sentences | 423 |
| Holdout sentences | 61 |
| Vocabulary | 255 tokens |
| Context | 5 tokens |
| Embedding width | 21 |
| Parameters | 32,385 |
| Training epochs | 5 |
| Quantization | Signed Q2.2 |
| Scoring multiplies | 5,355 |
| Holdout top one | 39.5% |
| Holdout top three | 60.0% |
| Holdout keystroke savings | 51.7% |
| Packed transport image | 16,193 bytes |
| Expanded working model | 32,385 bytes |
| All-context magnitude | 22 |
| Observed context magnitude | 16 |
| Proven score range | -1,060 to 1,015 |

Filling the one-byte token space reduces the embedding from 22 to 21
dimensions, yet uses nearly the entire 32 KiB weight budget. The harder,
broader holdout lowers headline accuracy, which is the expected cost of asking
a more general question. It still clears the original top-three gate by a
small margin and still misses the 60% keystroke-savings stretch gate.

Because an epoch is one pass through the corpus, expanding from 150 to 423
training sentences also changes the meaning of the epoch count. A fresh sweep
selects five epochs for the runnable artifact; later passes continue lowering
training loss without improving the held-out completion behaviour we care
about.

The current startup expands the working model at `$8000-$FE80`. The same
all-RAM loader, ROM-safe keyboard adapter, and direct-simulator parity tests
remain in use.

Run it:

```sh
make xroar-exp7
```

Run the non-interactive checks:

```sh
make model-test-exp7
make workbench-test-exp7
make xroar-test-exp7
```

## Interim conclusion

EXP-007 is ready for emulator demonstration and audience-driven exploration.
The larger model improves top-three accuracy over EXP-006 and makes sentence
punctuation visible, but it does not improve measured typing savings. Physical
hardware validation is the next acceptance boundary.

## Future boundary: 2 MiB CoCo 3 model

A future experiment may use Stacey's 2 MiB-expanded CoCo 3 and bank-switch
model segments through the GIME memory mapper. That will be CoCo 3-specific and
is deliberately outside EXP-007. EXP-007's all-RAM loader, explicit model
layout, and memory accounting should prepare for it without adding CoCo 3
banking assumptions to the CoCo 1 implementation.
