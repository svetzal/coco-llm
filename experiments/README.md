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
  — partially supported 8 KiB pretrained completion prototype; quality gate
  not yet met.
- [`EXP-007-all-ram-sentence-completion.md`](EXP-007-all-ram-sentence-completion.md)
  — runnable 32 KiB all-RAM, punctuation-aware completion experiment; physical
  hardware evidence remains outstanding.
- [`EXP-007-epoch-sweep.md`](EXP-007-epoch-sweep.md) — side experiment showing
  that training loss keeps falling after held-out Q2.2 quality peaks.

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
```

EXP-004 launches the stock-rate XRoar program and pauses before inference.
EXP-005 launches its own XRoar program, pauses after training, and provides an
interactive six-prompt workbench. Its larger training workload has not yet
been timed on physical stock-rate hardware. EXP-006 and EXP-007 launch
pretrained completion workbenches; say explicitly that the Mac trained their
weights and the CoCo performs integer inference.

| Experiment | Useful when the conversation asks… | Surface |
| --- | --- | --- |
| EXP-004 | Can the old machine really train it? | Interactive CoCo emulation |
| EXP-005 | Can starting words steer it? | Interactive prompted CoCo |
| EXP-006 | Can a pretrained model save typing? | 8 KiB completion workbench |
| EXP-007 | What changes with more memory and punctuation? | 32 KiB all-RAM |

EXP-001 through EXP-003 remain recorded as architectural evidence, but are no
longer in the runnable presentation menu. Presenter output deliberately shows
conclusions rather than dumping every sample. The recorded evidence remains
available for deeper inspection. The menu labels EXP-006 and EXP-007 as
emulator demonstrations until physical keyboard behaviour and stock-rate
latency are measured.
