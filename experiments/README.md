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
  supported floating-point token model; fixed-point and hardware work pending.
