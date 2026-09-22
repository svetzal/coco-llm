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
- `experiments/data/` — the fixed corpora and captured samples the experiments
  read.
- `presentation/` — the talk, live-demonstration choreography, and exhibit copy.
- `signage/` — the exhibit table's big-screen slideshow and the Raspberry Pi
  SD-card image that boots straight into it.
- `src/reference/` — the readable reference implementation, then its bit-exact
  fixed-point form.
- `src/6809/` — the 6809 implementation and CoCo platform adapters.
- `tools/` — the Python beside the 6809 code: it generates the 6809 data
  tables and test runners, drives the emulator captures, and exports every
  figure and trace the deck and the blog posts quote.
- `distribution/` — intentionally deferred until the project is ready to
  package for other people.

## Current status

Eighteen experiments form one evidence trail. Each is a file in
[`experiments/`](experiments/README.md) with a hypothesis, a procedure, the
measurements, and a conclusion.

| | | | |
| --- | --- | --- | --- |
| EXP-001 | the rejected character model | EXP-010 | the melody continuation |
| EXP-002 | the token model | EXP-011 | the context-editing attention head |
| EXP-003 | the fan-corpus bias runs | EXP-012 | the fake episode titles |
| EXP-004 | the live training run | EXP-013 | the game opponent that learns |
| EXP-005 | the prompted marketing completions | EXP-014 | the 6309 multiplier benchmark |
| EXP-006 | the 8 KiB completion workbench | EXP-015 | the faster-clock listening test |
| EXP-007 | the all-RAM sentence completer | EXP-016 | the register-resident loop |
| EXP-008 | the rejected adaptive opponent | EXP-017 | the wavetable voices |
| EXP-009 | the four-voice synthesizer | EXP-018 | the steady sample clock |

The reference, assembly, UI, and XRoar integration suite passes on macOS.
EXP-006, EXP-007 and EXP-011 are explicitly pretrained: the Mac trains and
exports their weights; the CoCo performs fixed-point inference. Timing on the
physical CoCo 1 is the one claim still deliberately unmade; the emulator is
proven and the hardware sessions are recorded in EXP-014, the hardware
session, and the sound experiments EXP-015 through EXP-018.

Read [`experiments/README.md`](experiments/README.md) for the experiment index,
[`research/model-design.md`](research/model-design.md) for the implemented
architectures, and
[`presentation/learning-journey.md`](presentation/learning-journey.md) for the
talk narrative.

## Getting started

This was built and is tested on macOS on Apple silicon. Everything below is
what that machine has; see "Platforms" for what is known about anything else.

### Install

| Tool | Why | macOS |
| --- | --- | --- |
| [uv](https://docs.astral.sh/uv/) | runs every Python step; installs Python 3.11+ and the pinned packages itself | `brew install uv` |
| [LWTOOLS](https://www.lwtools.ca/) (`lwasm`) | the 6809 and 6309 cross-assembler | `brew install lwtools` |
| [Rust](https://rustup.rs/) (`cargo`) | builds the pinned 6809 simulator that runs the assembly tests | `brew install rustup` then `rustup-init` |
| [XRoar](https://www.6809.org.uk/xroar/) | whole-machine CoCo emulation, for the interactive demos and the machine-level checks | `brew install xroar` |

The signage image and the exhibit cards need two more: Docker Desktop and
Google Chrome. Neither is needed for the model, the tests, or the talk.

### Build and test

```sh
make tools
make test
```

`make tools` checks for `lwasm` and `cargo`, then builds the
[gorsat/6809](https://github.com/gorsat/6809) simulator at a pinned revision
into `.tools/`. `make test` then does everything that needs no ROM images:
it syncs the Python environment, runs the formatter and linter, runs the
reference tests, assembles every CoCo binary, and runs the eleven assembly
test suites in the simulator, checking the 6809 against the reference
implementation byte for byte. It takes about twenty seconds.

### ROM images

The emulator targets need Tandy's ROMs, which are copyrighted and not in
this repository. Supply your own MAME-style archives and tell `make` where
they are:

| Archive | Members | CRC32 | Variable |
| --- | --- | --- | --- |
| `cocoe.zip` | `bas11.rom` (Color BASIC 1.1), `extbas10.rom` (Extended Color BASIC 1.0) | `6270955A`, `6111A086` | `COCO_ROM_ARCHIVE` |
| `coco3.zip` | `coco3.rom` (Super Extended Color BASIC) | `B4C88D6C` | `COCO3_ROM_ARCHIVE` |

```sh
make xroar-test COCO_ROM_ARCHIVE=/path/to/cocoe.zip
```

The ROMs are extracted once into the ignored `build/roms/` directory and
their checksums are verified before every emulator check. Without an archive
the ROM-gated targets stop with a message saying which variable to set.
Every `xroar*`, `block*`, `stage`, and hardware-experiment target is
ROM-gated; nothing under `make test` is.

### Machine-level checks

With the ROMs in place, the same binaries the table runs boot in a real-ROM
CoCo 1 and reach their keyboard prompts:

```sh
make xroar-test
make xroar-test-exp5
make xroar-test-exp6
make xroar-test-exp7
make xroar-test-attention
```

See [`research/toolchain.md`](research/toolchain.md) for the distinction
between CPU-level, machine-level, and physical-hardware evidence.

### Regenerating the deck's figures

Every number on a slide comes from a run. `make deck-figures` reruns the
reference model, exports the traces, and splices the figures into
`presentation/deck/index.html` between its `FIGURE` markers. The splicer
refuses to run over an uncommitted deck, because the hand-written copy lives
in the same file; commit first.

### The talk, the table, and the SD card

`make stage` launches the parked emulator windows for the talk and
`make block1` through `make block10` print each block's cues. `make sdcard`
builds the disk images and loose files for a CoCo SDC card, and
`make sdcard-install DEST=/Volumes/COCO` copies them to a mounted card and
verifies every byte. The one disk that needs Toolshed's `decb` reads it from
`DECB`, which you can set in the environment or on the command line. The big-screen slideshow and its Raspberry Pi image are
built from [`signage/`](signage/README.md). The talk itself is
[`presentation/runsheet.md`](presentation/runsheet.md).

### Platforms

**macOS, Apple silicon** is the only platform this has run on. The Makefile
defaults assume it: XRoar is looked up on `PATH` and then in Homebrew's keg,
`make block1` opens the deck with `open`, and the SD card mounts under
`/Volumes`.

**Linux** should work for the model, the tests, and the emulator, and is
untested. Every tool exists: uv and rustup install the same way, LWTOOLS
builds from source, and XRoar is packaged by most distributions or builds
from source. Set `XROAR=` if it is not on `PATH`, and `DEST=` for the SD
card. The Makefile needs GNU make and `unzip`. The two places that call
`open` are macOS-only and only affect the talk's stage commands and the
signage preview. The signage image builder additionally needs an arm64 host
and Docker with privileged containers, because the Pi's root filesystem is
customised in a native chroot.

**Windows** is untested and not expected to work natively: the Makefile
assumes a POSIX shell, `unzip`, and `nohup`. WSL2 is the plausible route and
follows the Linux notes, with the usual caveat that XRoar's window needs a
display the WSL session can reach.

**Physical hardware.** The programs load from a CoCo SDC. The CoCo 1 is a
32K machine; the CoCo 3 needs its own ROM archive, and its 6309 builds need
a 6309 fitted. The runsheet records which build goes on which machine.

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
`EXP` to list all seven demonstrations:

| Experiment | Demonstration | Command |
| --- | --- | --- |
| EXP-004 | Live 6809 training and generated names | `make present EXP=4` |
| EXP-005 | Prompted 1980s-style marketing language | `make present EXP=5` |
| EXP-006 | 8 KiB, four-word completion workbench | `make present EXP=6` |
| EXP-007 | 32 KiB all-RAM sentence completion | `make present EXP=7` |
| EXP-011 | Edit context without training | `make present EXP=11` |
| EXP-012 | Sixteen invented episode titles | `make present EXP=12` |
| EXP-013 | A game opponent that learns you | `make present EXP=13` |

## Watch it train in XRoar

```sh
make xroar
```

The first run extracts Color BASIC 1.1 and Extended Color BASIC 1.0 from your
ROM archive (see "ROM images" above) into `build/roms/`.

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
