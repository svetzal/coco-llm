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

The complete integer training and generation path now runs in 6809 assembly.
It matches all 580 final parameter bytes from the Python reference after twenty
epochs. Build the DECB binary with `make coco-bin`, verify the engine with
`make model-test`, or run the whole-machine demonstration with `make xroar`.
See
[`experiments/EXP-004-complete-6809-training.md`](experiments/EXP-004-complete-6809-training.md).

## Watch it train in XRoar

From Terminal:

```sh
cd ~/Work/Projects/Personal/coco-llm
make xroar
```

The first run extracts Stacey's local Color BASIC 1.1 and Extended Color BASIC
1.0 images from `~/OneDrive/CoCo/MAME/roms/cocoe.zip`. If that archive is still
an online-only OneDrive file, download it in Finder first.

XRoar opens as a stock-rate 32K NTSC CoCo 1 and loads the real DECB binary.
Watch for this sequence on the CoCo screen:

1. `COCO LLM TRAINING` in a full-width inverse title bar
2. `EPOCH 01 / 20 ACORN > ARCHIMEDES`, with the token pair changing for
   every training example and the epoch advancing through 20
3. `TRAINING COMPLETE`
4. `PRESS ANY KEY`, where the program waits for a new keyboard event
5. `GENERATING NAMES`, followed by five names appearing on separate rows
6. `GENERATION COMPLETE`

The text to the right of the count is the most recent context token and the
expected next token. Its 19-column field is overwritten in place, making the
58 examples in each epoch visible without scrolling the screen. The title bar
is the only inverse text; the changing training row remains normal text.

The deterministic parameter check still runs after training, but success is
not announced on screen. A failed check stops the demonstration with
`MODEL CHECK FAILED` instead of continuing into generation.

The current cycle projection is about 73 seconds for training. XRoar's `F12`
key runs at maximum speed while held; `Shift+F12` toggles maximum speed. Leave
those alone when you want to watch the stock-rate demonstration. Close the
XRoar window, or press `Control+C` in Terminal, when finished.

For a fast, headless correctness check instead of the visible demonstration:

```sh
make xroar-test
```
