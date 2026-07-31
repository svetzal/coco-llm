# EXP-007 side experiment: epoch sweep

## Status

Complete and reproducible. This side experiment measures the deployed EXP-007
architecture at eight training durations without changing its weights. The UI
mistake exposed by the experiment has been corrected.

## Question

Did 40 epochs earn its place, and does training longer keep improving the
model people actually use on the CoCo?

## Hypothesis

Very short runs will underfit. Additional epochs will initially improve
held-out completion, then reach a point where lower training loss no longer
means better held-out behaviour. The best epoch count may differ after the
model is quantized to the signed Q2.2 representation used by the CoCo.

## Procedure

Each row starts a fresh deterministic training run with seed 6809. Every run
uses the same 150 training sentences, 31 holdout sentences, 243-token
vocabulary, five-token context, 22 embedding dimensions, learning rate 0.01,
and batch size 32. The model is evaluated both at full precision and after the
signed Q2.2 quantization used by EXP-007.

Run the sweep with:

```sh
make exp007-epoch-sweep
```

The command writes its complete machine-readable evidence to
`build/exp007/epoch-sweep.json`.

## Results

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
evidence-selected optimum. Twenty epochs is the best candidate when top-three
suggestion quality is the priority. The runnable model remains at 40 epochs
until that product choice is made explicitly.

The punctuation symptom is an interface-policy lesson. The corrected workbench
now includes `<END>` in the ranked popover. Accepting it changes no sentence
text, removes any pending separator, closes the popover, and displays
`END OF PHRASE`. The model is telling us it is finished, and now people can see
that decision directly.
