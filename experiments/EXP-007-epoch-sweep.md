# EXP-007 side experiment: epoch sweep

## Status

Complete and reproducible. This side experiment measures the deployed EXP-007
architecture at several training durations. It now records both the original
150-sentence corpus and the expanded 423-sentence corpus. The UI mistake
exposed by the first sweep has been corrected.

## Question

Did 40 epochs earn its place, and does training longer keep improving the
model people actually use on the CoCo?

## Hypothesis

Very short runs will underfit. Additional epochs will initially improve
held-out completion, then reach a point where lower training loss no longer
means better held-out behaviour. The best epoch count may differ after the
model is quantized to the signed Q2.2 representation used by the CoCo.

## Procedure

Each row starts a fresh deterministic training run with seed 6809. Within a
sweep, every run uses the same corpus, vocabulary, five-token context, learning
rate 0.01, and batch size 32. The model is evaluated both at full precision and
after the signed Q2.2 quantization used by EXP-007.

Run the sweep with:

```sh
make exp007-epoch-sweep
```

The command writes its complete machine-readable evidence to
`build/exp007/epoch-sweep.json`.

## Baseline corpus results

The first sweep used 150 training sentences, 31 holdout sentences, 243 tokens,
and 22 embedding dimensions.

| Epochs | Train loss | Float top 3 | Q2.2 top 1 | Q2.2 top 3 | Saved |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 4.941 | 32.0% | 20.8% | 28.4% | 36.4% |
| 2 | 3.511 | 42.6% | 27.4% | 40.1% | 43.4% |
| 5 | 1.795 | 57.9% | 44.2% | 58.4% | 51.2% |
| 10 | 0.944 | 65.0% | 49.2% | 62.9% | 54.4% |
| 20 | 0.775 | 66.0% | 49.7% | **68.0%** | 53.9% |
| 40 | 0.751 | 66.0% | **50.8%** | 63.5% | 54.2% |
| 80 | 0.735 | 65.0% | 48.7% | 64.5% | 52.8% |
| 160 | **0.729** | 62.9% | 49.7% | 63.5% | **54.9%** |

Training loss falls at every checkpoint. Held-out quality does not. Twenty
epochs produces the strongest Q2.2 top-three result, while 40 narrowly wins
top-one accuracy and 160 narrowly wins keystroke savings. “Best” therefore
depends on the job we ask the model to do.

## Expanded corpus results

The current sweep uses 423 unique training sentences, 61 unique holdout
sentences, all 255 available token identifiers, and 21 embedding dimensions.
No holdout sentence appears in training and every holdout token is known.

| Epochs | Train loss | Float top 3 | Q2.2 top 1 | Q2.2 top 3 | Saved |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 4.144 | 40.9% | 25.2% | 40.7% | 40.8% |
| 2 | 2.861 | 52.9% | 31.1% | 52.0% | 47.4% |
| 3 | 2.205 | 58.1% | 36.5% | 58.1% | 49.4% |
| 4 | 1.768 | 59.5% | 38.4% | **60.2%** | 51.5% |
| 5 | 1.504 | **61.2%** | **39.5%** | 60.0% | 51.7% |
| 6 | 1.324 | 58.8% | 37.6% | 57.9% | **52.0%** |
| 8 | 1.137 | 60.2% | 34.1% | 56.2% | 49.0% |
| 10 | 1.062 | 59.1% | 35.3% | 55.3% | 49.6% |
| 20 | 0.970 | 58.4% | 37.9% | 56.9% | 51.3% |
| 40 | 0.930 | 56.7% | 33.2% | 51.8% | 49.8% |
| 80 | 0.917 | 53.9% | 35.5% | 56.2% | 50.1% |
| 160 | **0.907** | 49.9% | 26.1% | 46.4% | 46.7% |

Four epochs narrowly wins quantized top-three accuracy. Five is within
0.2 percentage points, while winning top-one accuracy and slightly improving
keystroke savings, so five is the selected runtime default. This is not a
claim that five is universally optimal. An epoch is a pass through the corpus;
the larger corpus performs almost three times as many training examples per
epoch as the baseline.

## Why punctuation appears after a period

EXP-007 trains `<END>` as the target after the terminal punctuation in every
sentence. The original 6809 popover excluded token zero, which is `<END>`,
because it is not an ordinary printable word. That policy was harmless in the
middle of a sentence, but misleading at its end: it hid the model's stop
decision and displayed the highest-scoring remaining token instead.

At 40 epochs, the Q2.2 model ranks `<END>` first for 30 of 31 held-out sentence
boundaries. For the 26 sentences ending in a period, it ranks `<END>` first 25
times. Once the UI removes `<END>`, the visible fallback after those periods is
punctuation in 11 cases:

| Visible fallback | Cases after a period |
| --- | ---: |
| `?` | 6 |
| `.` | 3 |
| `!` | 1 |
| `,` | 1 |

The question mark and comma are therefore usually not the model's chosen next
token. They are second choices exposed after the interface suppresses its
correct first choice.

The tiny additive model makes that fallback noisier. It learns overlapping
positional associations rather than a grammatical rule such as “one terminal
mark is enough.” Punctuation is also a frequent target in the small corpus, so
its output weights remain competitive when the stop token is removed.

## Conclusion

Forty epochs was a reasonable development checkpoint, but it was not an
evidence-selected optimum. On the baseline corpus, 20 epochs produced the best
top-three result. After the corpus grew, four and five epochs were strongest,
and the runnable model now uses five. The reversal is part of the lesson:
“epochs” cannot be compared without also saying how much data each epoch
contains.

The punctuation symptom is an interface-policy lesson. The corrected workbench
now includes `<END>` in the ranked popover. Accepting it changes no sentence
text, removes any pending separator, closes the popover, and displays
`END OF PHRASE`. The model is telling us it is finished, and now people can see
that decision directly.
