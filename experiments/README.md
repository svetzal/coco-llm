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

## Presentation commands

List the four audience-ready paths:

```sh
make present
```

Run any experiment by number:

```sh
make present EXP=1
make present EXP=2
make present EXP=3
make present EXP=4
```

The first three are concise, deterministic Mac reference demonstrations.
EXP-004 launches the stock-rate XRoar program and pauses before inference.

| Experiment | Useful when the conversation asks… | Surface |
| --- | --- | --- |
| EXP-001 | Why not train characters? | Rejected architecture and lower bound |
| EXP-002 | What difference does tokenization make? | Integer model comparison |
| EXP-003 | Can training data create bias? | Five-run comparison table |
| EXP-004 | Can the old machine really train it? | Interactive CoCo emulation |

The presenter output deliberately shows conclusions rather than dumping every
sample. The underlying experiment commands and recorded evidence remain
available for deeper inspection.
