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

## Promo

**CoCo-LLM: Definitely not large, barely even a language model, and the coolest
thing I've done yet on my CoCo**

Watch a Tandy Colour Computer from 1981 learn from random numbers, invent
plausible computer names, and complete fragments of 1980s-style marketing
language. The mechanism is small enough to inspect, the mistakes are visible,
and the limitations are part of the point.

The approved talk abstract, biography, and table copy live in
[`presentation/exhibit-copy.md`](presentation/exhibit-copy.md). That file is the
single source for public and printed wording.

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

## Original success target

From freshly randomized weights, a short training corpus should produce
recognizably corpus-shaped but novel computer names in no more than three
minutes on the CoCo 1.

EXP-001 through EXP-004 record how that target was tested and how the final
assembly implementation emerged. Emulator execution is proven; physical CoCo
1 timing remains deliberately unclaimed until it is measured.

## Repository map

- `research/` — durable findings, design decisions, sources, and hardware notes.
- `experiments/` — bounded hypotheses, procedures, measurements, and conclusions.
- `presentation/` — the talk, live-demonstration choreography, and exhibit copy.
- `src/reference/` — the readable reference implementation, then its bit-exact
  fixed-point form.
- `src/6809/` — the 6809 implementation and CoCo platform adapters.
- `distribution/` — intentionally deferred until the project is ready to
  package for other people.

## Current status

Eleven experiments now form one evidence trail:

- EXP-001 rejects an impractical character-level model.
- EXP-002 establishes the small token model and fixed-point direction.
- EXP-003 makes training-data selection and ordering bias visible.
- EXP-004 performs bit-exact training and generation in 6809 assembly.
- EXP-005 adds audience-selected starting phrases and marketing language.
- EXP-006 loads an 8 KiB pretrained model into an interactive completion UI.
- EXP-007 uses the CoCo 1 all-RAM map for a 32 KiB, 255-token,
  punctuation-aware sentence-completion model.
- EXP-008 tests online adaptation against a moving human target and accepts the
  table baseline's win.
- EXP-009 builds the fixed four-voice CoCo performer required for music work.
- EXP-010 tests prompted melody continuation and remains in progress.
- EXP-011 demonstrates contextual associative recall with a tiny attention
  head; its reference, quantization, 6809 parity, UI, and real-ROM emulator
  gates pass.

EXP-004 through EXP-007 and EXP-011 are individually runnable from the
presentation menu.
The complete reference, assembly, UI, and XRoar integration suite passes on
macOS. EXP-006, EXP-007, and EXP-011 are explicitly pretrained: the Mac trains
and exports their weights; the CoCo performs fixed-point inference. Physical
CoCo 1 and CoCo 3 timing and keyboard validation remain the next evidence
boundary, not a hidden completion claim.

Read [`experiments/README.md`](experiments/README.md) for the experiment index,
[`research/model-design.md`](research/model-design.md) for the implemented
architectures, and
[`presentation/learning-journey.md`](presentation/learning-journey.md) for the
talk narrative.

## Build and verify

Install the macOS toolchain and run every automated check:

```sh
brew install lwtools xroar
make tools
make test
make xroar-test
make xroar-test-exp5
make xroar-test-exp6
make xroar-test-exp7
make xroar-test-attention
```

The XRoar checks use Stacey's locally owned Tandy ROM images. See
[`research/toolchain.md`](research/toolchain.md) for ROM locations, checksums,
and the distinction between CPU-level, machine-level, and physical-hardware
evidence.

## Run a presentation experiment

For a conversation-driven presentation, list or run the audience-facing
experiments:

```sh
make present
make present EXP=4
make present EXP=5
make present EXP=11
```

The menu starts at EXP-004, the first complete 6809 learning loop. Run without
`EXP` to list all five demonstrations:

| Experiment | Demonstration | Command |
| --- | --- | --- |
| EXP-004 | Live 6809 training and generated names | `make present EXP=4` |
| EXP-005 | Prompted 1980s-style marketing language | `make present EXP=5` |
| EXP-006 | 8 KiB, four-word completion workbench | `make present EXP=6` |
| EXP-007 | 32 KiB all-RAM sentence completion | `make present EXP=7` |
| EXP-011 | Edit context without training | `make present EXP=11` |

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

1. `COCO LLM TRAINING`, left-aligned in a full-width dark title bar
2. `EPOCH 01 / 20` in black-on-green text
3. `# ACORN > ARCHIMEDES` on the full-width row below, changing for
   every training example
4. `TRAINING COMPLETE`
5. `PRESS ANY KEY`, where the program waits for a new keyboard event
6. A blank row, then `GENERATING NAMES`
7. Twelve generated lines filling the rest of the screen
8. `GENERATION COMPLETE`

The changing row shows both context tokens and the expected next token. All
58 examples fit within its 32 columns and are overwritten in place without
scrolling. The epoch and example rows use black text on the green background;
only the expected token uses green text on a dark field. `#` is the compact
on-screen form of the model's `<END>` boundary token.

Each inference line begins with the regular black-on-green seed `# # >`.
Everything produced by the model—including the final boundary `#`—appears
green-on-dark. A `+` in the final column means the genuine generated sequence
continued past the display width; inference itself was not truncated.

The deterministic parameter check still runs after training, but success is
not announced on screen. A failed check stops the demonstration with
`MODEL CHECK FAILED` instead of continuing into generation.

The current cycle model projects about 75 seconds for the complete run, but it
is not a validated emulator or physical-hardware stopwatch. Do not schedule a
presentation cue or screenshot from that estimate. XRoar's `F12` key runs at
maximum speed while held; `Shift+F12` toggles maximum speed. Leave those alone
when you want to watch the stock-rate demonstration. Close the XRoar window,
or press `Control+C` in Terminal, when finished.

For a fast, headless correctness check instead of the visible demonstration:

```sh
make xroar-test
```

## Prompt it interactively in XRoar

Experiment 5 has its own corpus, 380-parameter model, and DECB binary:

```sh
cd ~/Work/Projects/Personal/coco-llm
make xroar-exp5
```

After eighty training epochs, press any key to open the prompt workbench. Use
the CoCo Up and Down arrow keys to select one of six starting phrases and press
Enter to generate its continuation. The seed stays black-on-green, the
generated line is green-on-dark, and earlier completions remain visible.
Selection advances automatically, wrapping to the first prompt after the
sixth.

`make model-test-exp5` verifies all 760 final parameter bytes and the first
prompted completion in the direct 6809 simulator. `make xroar-test-exp5`
separately proves that the real-ROM whole-machine build reaches its post-
training keyboard handoff. Neither automated test is a physical-hardware
stopwatch.
