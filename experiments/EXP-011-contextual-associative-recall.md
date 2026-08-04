# EXP-011: Contextual associative recall

## Status

**Phase A supported; Phase B implemented and emulator-supported.** A
160-parameter, width-five key-value attention head recalls 100% of 4,096 novel
bindings after Q4.4 quantization. The result holds across two independent data
batches and ten initialization seeds. A parameter-only lookup scores 12.18%,
and an optimistic oracle limited to the last four of eight records scores
56.40%.

The reference implementation, deterministic data generator, baselines, width
sweep, quantization check, fixed-point 6809 inference core, interactive UI, and
tests exist. Run them with:

```sh
make exp011-sweep
make exp011-replicate
make attention-test
make attention-ui-test
make xroar-test-attention
make xroar-attention
```

The direct simulator matches all eight raw scores, winning slots, and copied
values for twelve novel contexts: 120 parity criteria in total. A second test
proves the initial query, first answer, context change, persistent query, new
answer, and slow-view winner. The real-ROM XRoar build reaches its keyboard
loop. Physical CoCo timing and keyboard behaviour remain unmeasured.

## Question

Can a tiny attention mechanism retrieve a fact supplied in its current context
when the fact changes every time, making it impossible to store the answer in
the model's parameters?

This follows the text-prediction experiments rather than the music work.
EXP-004 through EXP-007 show learned next-token prediction with fixed context
windows. EXP-011 asks whether the machine can instead use a new binding given
only for the current inference.

## Hypothesis

A single fixed-point key-value attention head of no more than 256 parameters
will answer at least 99% of held-out associative-recall queries across five
initialization seeds, while:

- the best parameter-only key-to-value lookup remains within two percentage
  points of chance;
- an oracle limited to the final four of eight context records remains at
  least thirty percentage points below attention;
- signed Q4.4 quantization changes accuracy by no more than 0.5 percentage
  points; and
- every fixed-point dot product fits a signed 16-bit accumulator.

## Null result to respect

If a global lookup learns the task, the supposedly contextual information has
leaked into the parameters. If a short-window oracle matches attention, the
experiment is only demonstrating recency. If attention succeeds only for one
initialization or loses the result after quantization, it has not earned a
6809 port.

## Task

Each example supplies eight key-value records and then repeats one key as a
query:

```text
K12 = V3
K04 = V0
K09 = V6
...
QUERY K04 > V0
```

There are sixteen possible keys and eight possible values. Every context uses
eight distinct keys and all eight values in a fresh random permutation. The
queried record is selected uniformly from the eight positions.

The binding changes between examples. `K04` may map to `V0` now and `V7` in
the next example. Training can therefore teach the model how to match a query
to a record, but cannot teach it a durable answer for any key.

Training and test sets use independent deterministic random streams with 4,096
examples each. The test contexts are generated separately and are not a stored
language corpus.

## Mechanism

The model has a learned query vector and learned key vector for each of the
sixteen key tokens. For every memory record it calculates:

```text
score(record) = query_vector(query) dot key_vector(record.key)
```

Softmax over the eight scores supplies attention probabilities during
training. At inference, the highest score selects a record and its value is
copied directly. Softmax is unnecessary for that ranking, as in EXP-006 and
EXP-007.

This is genuine content-addressed key-value attention, but it is deliberately
not described as a transformer. It has no residual stream, layer
normalization, feed-forward layer, output projection, positional encoding, or
stack of causal self-attention blocks. The value vectors are one-hot records
rather than learned token representations. Query and key projections are
folded into two small embedding tables.

Those omissions isolate the new mechanism: information can determine an
answer because it is present in the current context, not because training
stored that answer in the weights.

## Baselines

The experiment includes deliberately strong and deliberately diagnostic
baselines:

1. **Chance** chooses one of eight values: 12.5% expected accuracy.
2. **Global parameter lookup** records the most common training value for each
   query key. It detects leakage or a biased generator.
3. **Tail oracle** answers perfectly if the queried binding appears within its
   visible final one, two, or four records. Otherwise it falls back to the
   global lookup. This is more capable than the existing additive fixed-window
   model and therefore gives that family an optimistic ceiling.
4. **Untrained attention** is a negative control for the learned matching
   operation.

## Phase A gates

Proceed to a 6809 inference core only if all of the following hold:

- worst trained accuracy across seeds 6809 through 6813 is at least 99%;
- global lookup is no more than 14.5%;
- attention beats the four-record tail oracle by at least thirty points;
- Q4.4 accuracy is within 0.5 points of floating point;
- the smallest passing width uses no more than 256 parameters; and
- signed-byte operands and signed 16-bit dot products are sufficient.

## Phase A result

The selected width-five model produces on the development batch:

| Method | Test accuracy |
| --- | ---: |
| Chance | 12.50% |
| Global parameter lookup | 12.18% |
| Oracle, last one record | 23.24% |
| Oracle, last two records | 34.03% |
| Oracle, last four records | 56.40% |
| Attention, untrained | 22.24% |
| Attention, trained | **100.00%** |
| Attention, signed Q4.4 | **100.00%** |

The selected seed's test cross-entropy falls from 2.923 to 0.116 bits per
record. Q4.4 quantization changes it to 0.117 bits.

The width sweep uses the predeclared five initialization seeds:

| Width | Parameters | Worst float | Worst Q4.4 |
| ---: | ---: | ---: | ---: |
| 2 | 64 | 75.22% | 74.34% |
| 3 | 96 | 96.75% | 96.75% |
| **4** | **128** | **100.00%** | **100.00%** |
| 5 | 160 | 100.00% | 100.00% |
| 6 | 192 | 100.00% | 100.00% |
| 8 | 256 | 100.00% | 100.00% |

This first sweep was exploratory: the task, candidates, and gates were designed
in the same setup session. The selected architecture was therefore replicated
on new training and test streams with five new initialization seeds:

| Width | Parameters | Worst float | Worst Q4.4 |
| ---: | ---: | ---: | ---: |
| 2 | 64 | 77.78% | 78.22% |
| 3 | 96 | 100.00% | 100.00% |
| 4 | 128 | **97.29%** | **97.29%** |
| **5** | **160** | **100.00%** | **100.00%** |
| 6 | 192 | 100.00% | 100.00% |
| 8 | 256 | 100.00% | 100.00% |

The replication rejects width four: one fresh initialization falls below the
99% gate. Width five is the smallest candidate that clears the gate in both
sweeps, across all ten initializations. On the replication batch the global
lookup scores 12.45%, the four-record oracle scores 56.13%, and the selected
head again scores 100% before and after quantization.

Across the ten width-five models, Q4.4 operands range from -61 to 61 and all
256 possible query-key dot products range from -3,512 to 3,641. Signed bytes
and a signed 16-bit accumulator are therefore sufficient.

Every declared Phase A gate passes.

## What the result means

The result is not evidence that the model learned facts. It learned a matching
operation. The facts remain in the eight records and disappear when that
context is replaced.

The discontinuity against the baselines is the point. A global parameter
lookup cannot know a mapping that changes every example. A four-record window
cannot see half of the possible answers. Attention can scan all eight records,
select by content rather than position, and copy the associated value.

That is the smallest honest bridge this project has yet built from ordinary
next-token prediction toward the way modern LLMs use prompt context.

## Projected CoCo inference

The selected model stores 160 signed Q4.4 bytes: sixteen query vectors and
sixteen key vectors, each five bytes wide. One query over eight records costs
40 signed 8-by-8 multiply-accumulates. At the existing rough projection of 35
cycles per signed multiply-accumulate, scoring costs about 1,400 cycles, or
1.6 ms at 0.89 MHz, before record traversal and display.

The current context needs sixteen token bytes for eight key-value records plus
one query byte. No softmax, probability table, or value matrix is needed at
inference. The projected core fits easily beside a simple CoCo interface, but
these are arithmetic projections rather than measurements.

## Implemented CoCo interface

The 32-by-16 interface uses three separate screens instead of presenting every
idea at once. The first establishes eight temporary key-value facts and one
question. Enter replaces it with a focused answer screen showing the best
match, copied value, and `MODEL 751B DID NOT CHANGE`. `S` returns to a visibly
changed fact set while preserving both the question and model identifier. Up
and Down remain available as a secondary way to choose another question.

The selected question uses `>` and the best match uses `*` as well as dark
text, so neither state is communicated by colour alone.

`S` cycles through four deterministic shuffled contexts while preserving the
query token. The selected computer therefore changes row and code without any
change to model `751B`. `V` progressively discloses an explicitly labelled
`SLOW VIEW`: each Enter press reveals one score and the best record so far. The
computation has already happened; the pacing belongs to the explanation, not
the inference.

The presenter runbook and exact Lisa path live in
[`presentation/exp011-demo-script.md`](../presentation/exp011-demo-script.md).

## Next step

Run the complete interaction on a physical stock-rate CoCo 1 and the CoCo 3
HDMI presentation path. Measure query latency, verify every keyboard control,
and inspect the slow-view screen. Until then, describe this as emulator and
direct-simulator evidence: the CoCo is consulting its current context, not
adding the assignments to its trained knowledge.
