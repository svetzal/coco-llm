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

## Presentation commands

List the audience-ready paths, beginning with the first complete 6809 run:

```sh
make present
```

Run either presentation experiment:

```sh
make present EXP=4
make present EXP=5
```

EXP-004 launches the stock-rate XRoar program and pauses before inference.
EXP-005 launches its own XRoar program, pauses after training, and provides an
interactive six-prompt workbench. Its larger training workload has not yet
been timed on physical stock-rate hardware.

| Experiment | Useful when the conversation asks… | Surface |
| --- | --- | --- |
| EXP-004 | Can the old machine really train it? | Interactive CoCo emulation |
| EXP-005 | Can starting words steer it? | Interactive prompted CoCo |

EXP-001 through EXP-003 remain recorded as architectural evidence, but are no
longer in the runnable presentation menu. Presenter output deliberately shows
conclusions rather than dumping every sample. The recorded evidence remains
available for deeper inspection.
