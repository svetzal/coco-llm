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

## Never write a bare EXP number

`EXP-004` names nothing. A reader who does not already hold thirteen experiment
numbers in their head has to go and look it up, and working memory is small
enough that they will have lost the sentence by the time they get back.

Every reference to an experiment carries two or three words saying what it is,
on first use in a document, in every table row, and every time it is the
subject of a claim in conversation. `EXP-004, the live training run` costs four
words. Making the reader leave costs the paragraph.

The same applies to any other symbol that stands in for a thing: a bug number,
an issue identifier, a run label, a commit hash.

Use these glosses, so the short names stay stable across documents:

| | Gloss |
| --- | --- |
| EXP-001 | the rejected character model |
| EXP-002 | the token model |
| EXP-003 | the fan-corpus bias runs |
| EXP-004 | the live training run |
| EXP-005 | the prompted marketing completions |
| EXP-006 | the 8 KiB completion workbench |
| EXP-007 | the all-RAM sentence completer |
| EXP-008 | the rejected adaptive opponent |
| EXP-009 | the four-voice synthesizer |
| EXP-010 | the melody continuation |
| EXP-011 | the context-editing attention head |
| EXP-012 | the fake episode titles |
| EXP-013 | the game opponent that learns |
| EXP-014 | the 6309 multiplier benchmark |

Shorten a gloss where the sentence already supplies the context, but do not
drop it. Add a row here when an experiment is added.

## Lesson and demonstration design

Make causality visible before adding explanation or metaphor. A learner should
be able to point to the source of a value, the action that changed it, the state
that was modified, and the resulting behaviour. Do not use a magic shuffle,
silent reassignment, or presenter narration to bridge a causal step the
interface does not show.

When teaching a distinction such as training versus context:

1. Label the relevant state stores in the interface (`WEIGHTS`, `CONTEXT`,
   working state) and keep those labels visible at the moment of change.
2. Let a person perform the material action. Prefer an explicit edit over a
   button that swaps in prepared state.
3. Show before and after values, name what changed, and name what did not.
4. Repeat the same query or operation so the changed outcome has one visible
   cause.
5. Test both the intended change and the claimed invariant—for example, the
   context byte changed while the weight bytes remained unchanged.

Introduce one new idea per screen or beat. Establish the input first, show the
outcome second, and reveal internal arithmetic only as optional depth. The
primary path should teach the concept without requiring the slow or diagnostic
view.

Prefer the project's sustained vintage-computer example over a new metaphor.
A metaphor may reinforce an already-visible mechanism; it must not replace the
missing mechanism or invent a second scenario the audience must decode.

Treat audience confusion as evidence about the artifact, not merely a cue to
rewrite the script. If a reasonable viewer asks where a value came from or why
it changed, improve the interface and add a deterministic check that protects
the clarified causal path. Keep screen language, presenter words, controls,
tests, and recorded claims aligned.

## Repository practice

- Work directly on `main`.
- Make small, scoped commits.
- Keep generated build products out of source control unless they are deliberate
  test fixtures.
- Do not create `distribution/` until there is a tested artifact worth
  distributing.
- Cite primary sources where available.
