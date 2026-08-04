# Experiments

Experiments turn architectural uncertainty into recorded evidence.

Each experiment should contain:

- a falsifiable hypothesis;
- the smallest procedure capable of testing it;
- fixed inputs and environment details;
- measurements and generated samples;
- a conclusion;
- the decision or next experiment that follows.

Use the filename pattern `EXP-NNN-short-name.md`. Do not rewrite an experiment's
original hypothesis after observing the result. Append evidence and conclusions
so the learning remains visible.

Current experiments:

- [`EXP-001-model-feasibility.md`](EXP-001-model-feasibility.md) — rejected
  character-level candidate.
- [`EXP-002-token-model-feasibility.md`](EXP-002-token-model-feasibility.md) —
  supported floating-point and integer token model.
- [`EXP-003-training-data-bias.md`](EXP-003-training-data-bias.md) — controlled
  fan-corpus and ordering-bias demonstration.
- [`EXP-004-complete-6809-training.md`](EXP-004-complete-6809-training.md) —
  complete bit-exact assembly training, generation, and initial timing evidence.
- [`EXP-005-prompted-marketing-language.md`](EXP-005-prompted-marketing-language.md)
  — expanded advertising vocabulary and visible two-word prompting.
- [`EXP-006-pretrained-tab-completion.md`](EXP-006-pretrained-tab-completion.md)
  — partially supported 8 KiB pretrained completion prototype; its original
  quality gate failed, but its task-level usefulness and runnable UI make the
  failure presentable.
- [`EXP-007-all-ram-sentence-completion.md`](EXP-007-all-ram-sentence-completion.md)
  — runnable 32 KiB all-RAM, punctuation-aware completion experiment; physical
  hardware evidence remains outstanding.
- [`EXP-007-epoch-sweep.md`](EXP-007-epoch-sweep.md) — side experiment showing
  that training loss keeps falling after held-out Q2.2 quality peaks.
- [`EXP-008-adaptive-opponent.md`](EXP-008-adaptive-opponent.md) — rejected
  adaptive-opponent experiment. On three recorded human sessions a ninety-byte
  order-1 frequency table predicts a live player better than every neural
  candidate, so the declared null result triggered and the 6809 port was not
  attempted.
- [`EXP-009-four-voice-music.md`](EXP-009-four-voice-music.md) — four-voice
  software synthesizer for a stock CoCo 1, built as the performer for a
  possible tracker-generation direction. Records why the HSYNC interrupt
  cannot drive an audio sample clock on this machine.
- [`EXP-010-melody-continuation.md`](EXP-010-melody-continuation.md) — planned
  experiment in which the audience enters an opening bar and the CoCo composes
  and performs a continuation. Melody is scale degrees conditioned on mode,
  metre, beat and chord, so a wrong note is impossible by construction.
  Records corpus vetting, including one dataset whose licence forbids LLM
  training. Phase A passed: the model beats the strongest table by 0.243
  bits per row, and situational context supplies most of that.
- [`EXP-011-contextual-associative-recall.md`](EXP-011-contextual-associative-recall.md)
  — supported reference experiment in content-addressed key-value attention.
  A 160-parameter head recalls 100% of novel contextual bindings across two
  data batches and ten seeds after Q4.4 quantization. Its fixed-point 6809
  inference and guided facts/answer/context UI pass direct and real-ROM
  emulator gates. A slow attention replay is available as optional depth;
  physical hardware remains unverified.

## Presentation commands

List the audience-ready paths, beginning with the first complete 6809 run:

```sh
make present
```

Run any presentation experiment:

```sh
make present EXP=4
make present EXP=5
make present EXP=6
make present EXP=7
make present EXP=11
```

EXP-004 launches the stock-rate-limited XRoar program and pauses before
inference.
EXP-005 launches its own XRoar program, pauses after training, and provides an
interactive six-prompt workbench. Its larger training workload has not yet
been timed on physical stock-rate hardware. EXP-006 and EXP-007 launch
pretrained completion workbenches; say explicitly that the Mac trained their
weights and the CoCo performs integer inference.
EXP-011 launches a guided temporary-map demonstration. Its Mac-trained
160-byte head runs fixed-point scoring on the CoCo. A museum scenario gives
the values a visible purpose: each computer exhibit has a shelf on today's
map. The primary path reveals the map, location, and a replacement map
separately; `V` optionally replays the stored scores at presentation speed.

| Experiment | Useful when the conversation asks… | Surface |
| --- | --- | --- |
| EXP-004 | Can the old machine really train it? | Interactive CoCo emulation |
| EXP-005 | Can starting words steer it? | Interactive prompted CoCo |
| EXP-006 | Can a pretrained model save typing? | 8 KiB completion workbench |
| EXP-007 | What changes with more memory and punctuation? | 32 KiB all-RAM |
| EXP-011 | Can it use a fact supplied right now? | Context-attention bench |

EXP-001 through EXP-003 remain recorded as architectural evidence, but are no
longer in the runnable presentation menu. Presenter output deliberately shows
conclusions rather than dumping every sample. The recorded evidence remains
available for deeper inspection. The menu labels EXP-006, EXP-007, and EXP-011
as emulator demonstrations until physical keyboard behaviour and stock-rate
latency are measured.
