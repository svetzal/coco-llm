# Project guidance

## Purpose

Build an understandable language model that demonstrably trains on a stock
CoCo 1. The code, research, experiments, and presentation are all parts of the
same product: helping people see what language models do, what they do not do,
and how people can use them with practical expectations.

## Working principles

- Optimize for learning value before novelty or benchmark performance.
- Keep the model mathematically honest. Simplifications must be named and
  explained.
- Never hide training or inference on modern hardware during a demonstration.
- Treat the CoCo 1 at its normal clock rate as the performance contract.
- Keep the computational core bit-exact across the reference implementation,
  emulator, CoCo 1, and CoCo 3.
- Prefer deterministic seeds, fixed corpora, checksums, and test vectors.
- Use physical hardware to validate timing and behaviour before making public
  claims.
- Keep platform display and I/O code outside the learning engine.
- Record uncertain ideas as experiments rather than quietly turning them into
  architecture.

## Evidence loop

For each material technical decision:

1. State a falsifiable hypothesis in `experiments/`.
2. Implement the smallest test in `src/reference/`.
3. Record quality, memory, operation counts, and timing.
4. Port only the parts supported by evidence.
5. Capture the conclusion and update durable research.

An experiment is complete only when its evidence and conclusion are recorded.

## Presentation integrity

The sustained example is a model learning vintage-computer names. Return to it
throughout the presentation rather than introducing unrelated AI examples.

Keep these distinctions explicit:

- prediction is not understanding;
- stored parameters are not a database of copied sentences;
- useful output is not necessarily correct output;
- automating a task is not assuming human purpose or accountability;
- this model shares the learning objective of modern generative language
  models, but not their transformer architecture or scale.

## Repository practice

- Work directly on `main`.
- Make small, scoped commits.
- Keep generated build products out of source control unless they are deliberate
  test fixtures.
- Do not create `distribution/` until there is a tested artifact worth
  distributing.
- Cite primary sources where available.
