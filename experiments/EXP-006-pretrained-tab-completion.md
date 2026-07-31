# EXP-006: Pretrained tab completion

## Question

Can a model trained on the Mac, compressed into no more than 8 KiB of
one-byte weights, provide useful next-word tab completion on a stock CoCo?

## Hypothesis

A bounded word-level neural model with four words of context will:

- fit in 8,192 signed one-byte parameters;
- achieve at least 70% top-three accuracy on unseen phrases whose words are in
  its vocabulary;
- save at least 35% of the keystrokes needed to type held-out words when Tab
  accepts the best prefix-compatible suggestion;
- lose no more than five percentage points of top-three accuracy when its
  weights are quantized to signed Q4.4;
- beat a frequency-only predictor on top-three accuracy and keystroke savings.

An n-gram model is included as a non-neural baseline. If it is materially
better than the quantized neural candidates, the neural model is not supported
for the CoCo workbench merely because it fits the story.

## Frozen setup

- 8,192-byte maximum stored-weight budget;
- word-level tokens plus one boundary token;
- four-token context;
- fixed training and held-out phrase files;
- held-out phrases contain no words absent from training;
- deterministic seed 6809;
- full-precision Mac training followed by signed Q4.4 weight simulation;
- additive embedding and one-hidden-layer neural candidates;
- frequency-only and backoff n-gram baselines;
- next-word top-one, top-three, cross-entropy, and prefix-aware keystroke
  metrics.

The training source is
[`data/EXP-006-completion-training.txt`](data/EXP-006-completion-training.txt).
The held-out source is
[`data/EXP-006-completion-holdout.txt`](data/EXP-006-completion-holdout.txt).

## Keystroke metric

For each held-out word, the evaluator types the shortest prefix that makes the
intended word the model's highest-scoring compatible suggestion, then counts
one Tab keystroke to accept it. If this would take as many keystrokes as typing
the whole word, the evaluator types the word normally. Boundary tokens are not
counted. This is an offline simulation of the proposed interaction, not yet a
measurement of a CoCo user interface.

## Decision gate

Only a neural candidate that satisfies the hypothesis proceeds to a 6809
inference implementation. The first CoCo artifact will load an exported model
rather than train it and will expose next-word suggestions after the user
presses Tab. Physical-hardware timing remains a separate evidence step.

## Evidence

Recorded on the macOS reference environment:

- 147 training phrases and 24 held-out phrases;
- 796 training examples and 132 held-out examples;
- 178 tokens, including the boundary token;
- twenty Mac-training epochs;
- 8,188 one-byte parameters in the selected additive model;
- four padding bytes in the fixed 8,192-byte image.

| Candidate | Top one | Top three | Keystrokes saved | Cross-entropy |
| --- | ---: | ---: | ---: | ---: |
| Frequency only | 16.7% | 25.0% | 47.9% | 3.979 |
| Backoff n-gram | 34.3% | 49.1% | 55.8% | 3.776 |
| Additive float | 38.0% | 59.3% | 58.8% | 2.039 |
| Additive Q4.4 | 38.0% | 59.3% | 58.8% | 2.049 |
| Hidden float | 38.9% | 58.3% | 58.0% | 2.948 |
| Hidden Q4.4 | 41.7% | 56.5% | 58.0% | 2.957 |

The 70% top-three criterion failed. The other four criteria passed:

- the model fits the 8,192-byte weight budget;
- it saves more than 35% of word-entry keystrokes;
- Q4.4 quantization loses no top-three accuracy in the selected model;
- it beats the frequency predictor on both task metrics.

The simpler additive model was selected for the engineering prototype. It
outperformed the hidden model and maps especially well to the 6809:

| Component | Shape | Byte offset | Bytes |
| --- | ---: | ---: | ---: |
| Positional embeddings | 4 × 178 × 9 | 0 | 6,408 |
| Output weights | 178 × 9 | 6,408 | 1,602 |
| Output biases | 178 | 8,010 | 178 |
| Padding | — | 8,188 | 4 |
| **Image** | — | — | **8,192** |

Each stored value is a signed Q4.4 byte. Four positional embeddings add into a
nine-byte context vector. Exhaustive range analysis over every possible
four-token combination bounds those values to -99 through 105, so they remain
valid signed 8-bit operands. Scoring all outputs requires 1,602 model
multiplications. Four additional `MUL` instructions locate the embedding rows.

Representative top-three completions from the exported integer model:

| Typed context | Suggestions |
| --- | --- |
| `PRESS TAB TO` | `COMPLETE`, `ACCEPT`, `STOP` |
| `LOAD THE` | `PROGRAM`, `FILE`, `GAME` |
| `THE COMMODORE` | `64`, `VIC`, `AMIGA` |
| `THE MODEL PREDICTS` | `THE`, `BASIC`, `EXTENDED` |
| `HUMANS CHECK THE` | `COMPUTER`, `PROGRAM`, `COLOR` |

## Exported model

Run:

```sh
make exp006-model
```

This creates ignored development artifacts under `build/exp006/`:

- `weights.bin` — fixed 8,192-byte model image;
- `weights.decb` — a DECB memory image loading at `$6000`;
- `vocabulary.txt` — the ordered 178-token vocabulary;
- `manifest.json` — shapes, offsets, checksum, range proof, and workload;
- `test-vectors.json` — contexts and expected integer rankings;
- `model_data.inc` — assembly constants for parity tests.

The exported image SHA-256 is
`a9c224bd3acd2a9b969189cde2878394558927a81accbd2c4a2a5f68aa3ff4b4`.

## 6809 evidence

`src/6809/completion_inference.asm` implements integer inference without
softmax. Ranking logits is mathematically sufficient because softmax preserves
their order. Its signed 8×8 wrapper uses one native unsigned `MUL` followed by
the required two's-complement corrections.

Run:

```sh
make model-test-exp6
```

The direct simulator verifies:

- all nine context-vector bytes for `PRESS TAB TO`;
- the three expected token identifiers for `COMPLETE`, `ACCEPT`, and `STOP`;
- 36,183 executed instructions for the complete test program.

The simulator is not cycle-accurate, so this is parity and instruction-count
evidence, not a stock-CoCo latency measurement.

## Conclusion

The original hypothesis is not supported because its top-three condition was
conjunctive and failed.

The more important task-level result is promising: a quantized 8 KiB neural
model saves 58.8% of held-out word keystrokes, beats both baselines, and now has
a bit-exact 6809 inference core. It is an engineering prototype, not yet a
presentation experiment.

The next step is an interactive CoCo workbench that types a phrase, invokes
the predictor with Tab, and cycles the three prefix-compatible suggestions.
It should not enter the `make present` menu until XRoar verifies the interaction
and timing. Before calling the quality result a success, either define a
task-focused acceptance criterion in a follow-up experiment or revise the
corpus and vocabulary without rewriting this failed hypothesis.
