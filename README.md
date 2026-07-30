# CoCo LLM

CoCo LLM asks a deliberately playful question:

> Could a 45-year-old home computer train a language model in front of a live
> audience?

The project will build a small, causal, token-level neural language model that
trains from random weights on a stock Motorola 6809E. The primary target is a
Radio Shack TRS-80 Color Computer 1. A Color Computer 3 will provide a
compatible backup and a presentation-friendly HDMI display.

The model is not large and it is not a transformer. It is an honest language
model built around the same essential learning loop as contemporary generative
language models:

1. Turn text into tokens.
2. Predict the next token.
3. Measure the prediction error.
4. Propagate that error through the network.
5. Adjust the parameters.
6. Repeat, then generate one token at a time.

## Project thesis

The machine will learn that tokens such as `AMIGA` can plausibly follow
`COMMODORE` without knowing what either word means or what a computer is.

That single example supports the whole learning journey. It makes the mechanics
of language-model training visible, exposes the difference between fluent
prediction and understanding, and creates room for a grounded conversation
about using modern language models well.

The intended conclusion is neither fear nor hype. Language models can be
remarkably useful when people give them a bounded job, useful context, and
appropriate verification. They do not supply human purpose, responsibility,
judgement, or lived context.

The project also makes training-data choices visible. Identical models trained
as Apple, Commodore, and Tandy fans learn visibly different output
distributions. Combining the examples demonstrates that representation,
weighting, and presentation order can all influence the result.

## Hardware contract

- **Primary:** CoCo 1, MC6809E at approximately 0.89 MHz.
- **Backup and presentation:** CoCo 3 with HDMI output.
- **Compatibility:** The learning engine must be bit-for-bit identical on both
  systems.
- **CoCo 3 fast mode:** Permitted as a clearly labelled demonstration option,
  never used to conceal a CoCo 1 performance failure.
- **Loading:** CoCo SDC or FujiNet.
- **Development:** Cross-compiled and tested primarily on macOS, with emulation
  and repeatable test vectors. Physical hardware remains the final authority.

## Initial success target

From freshly randomized weights, a short training corpus should produce
recognizably corpus-shaped but novel computer names in no more than three
minutes on the CoCo 1.

The first experiment will test that target before the project commits to an
assembly implementation.

## Repository map

- `research/` — durable findings, design decisions, sources, and hardware notes.
- `experiments/` — bounded hypotheses, procedures, measurements, and conclusions.
- `presentation/` — the talk, live-demonstration choreography, and exhibit copy.
- `src/reference/` — the readable reference implementation, then its bit-exact
  fixed-point form.
- `src/6809/` — the 6809 implementation and CoCo platform adapters.
- `distribution/` — intentionally deferred until the project is ready to
  package for other people.

## Current direction

The first character-level candidate was rejected by EXP-001 before assembly:
the 6809's raw multiplication time consumed nearly the entire demonstration
budget. The current candidate uses 29 visible tokens, a two-token context,
three-value positional embeddings, 290 trainable parameters, and integer-only
training. See
[`research/model-design.md`](research/model-design.md) and
[`experiments/EXP-002-token-model-feasibility.md`](experiments/EXP-002-token-model-feasibility.md).

The controlled bias demonstration is recorded in
[`experiments/EXP-003-training-data-bias.md`](experiments/EXP-003-training-data-bias.md).
