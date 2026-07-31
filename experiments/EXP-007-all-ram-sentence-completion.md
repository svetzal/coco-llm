# EXP-007: All-RAM sentence completion

## Status

In progress. The baseline capacity sweep is reproducible; the expanded
punctuated corpus, all-RAM loader, 6809 port, and physical timing evidence do
not yet exist.

## Question

Can a 64 KiB CoCo 1 use an all-RAM memory map to run a substantially larger,
punctuation-aware completion model that produces short sentences while
remaining responsive enough for an interactive demonstration?

## Hypothesis

A 255-token additive Q4.4 model with five tokens of context will make the
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

The additive model stores one signed Q4.4 byte per parameter:

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

A contiguous 48 KiB image fits exactly at:

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

Loading bytes beneath the normal ROM window is a separate acceptance test. A
model that works only because an emulator preloaded hidden RAM does not satisfy
the hardware contract.

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
- Q4.4 quantization does not lose more than one percentage point;
- every possible context vector remains in signed 8-bit range;
- the chosen model fits its declared 32, 40, or 48 KiB image; and
- stock-rate CoCo 1 latency is measured and explicitly accepted.

## Future boundary: 2 MiB CoCo 3 model

A future experiment may use Stacey's 2 MiB-expanded CoCo 3 and bank-switch
model segments through the GIME memory mapper. That will be CoCo 3-specific and
is deliberately outside EXP-007. EXP-007's all-RAM loader, explicit model
layout, and memory accounting should prepare for it without adding CoCo 3
banking assumptions to the CoCo 1 implementation.
