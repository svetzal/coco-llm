# 6809 implementation

This folder contains the first complete bit-exact training implementation:

- `experiments/experiment_004.asm` — the complete EXP-004 lesson driver:
  train, verify, then generate a sampled gallery from a boundary seed;
- `experiments/experiment_005.asm` — the complete EXP-005 lesson driver:
  train the expanded model, then run prompted greedy inference;
- `model_core.asm` — initialization, the shared forward pass, approximate
  softmax, fixed-point arithmetic, and verification;
- `model_storage.asm` — shared parameters and working memory, kept at the end
  of each assembled image;
- `training.asm` — epoch and example loops, error calculation, backpropagation,
  and parameter updates;
- `inference.asm` — the shared next-token loop plus reusable sampled and greedy
  selection functions;
- `screen.asm` — CoCo VDG screen setup, text rendering, token formatting, and
  status messages;
- `completion_screen.asm` — the experiment-neutral VDG completion screen,
  word-wrapped editor rendering, and save/restore suggestion popover;
- `completion_editor.asm` — the shared keyboard-driven completion controller;
- `completion_policy_exp6.asm` — EXP-006's four-word parser, prefix matching,
  model call, and accepted-word spacing;
- `completion_inference_exp7.asm` — the five-token, 22-dimension EXP-007
  integer scorer;
- `completion_policy_exp7.asm` — punctuation tokenization and spacing plus the
  all-RAM keyboard adapter;
- `experiments/sample_gallery.asm` and
  `experiments/prompt_workbench.asm` — the lesson-specific presentation shells;
- `coco_llm.asm` — the writable CoCo program at `$2000`;
- `coco_llm_exp5.asm` — the prompted advertising-language variant;
- `tests/model_test.asm` and `tests/model_exp5_test.asm` — direct-simulator
  wrappers.

Each experiment driver is the composition root. Its short `start` routine calls
the same screen initialization, model initialization, training, and
verification functions before delegating to its lesson-specific presentation.
Training and inference deliberately share `model_core.asm`'s `forward` routine:
training uses the resulting probabilities to calculate errors and update
parameters, while inference uses them to choose the next token.

The drivers also name the few policies that genuinely differ:

- EXP-004 uses the measured-safe 8×16 training multiply, suppresses an early
  boundary token, and samples from the probability distribution;
- EXP-005 uses the full 16×16 training multiply, accepts an audience-selected
  context without a minimum length, and chooses the highest-probability token.

There are no experiment-number conditionals in the shared engine. This split
keeps each new lesson explicit without duplicating the model mathematics.

The completion workbench follows the same rule. Its screen and editor use
small experiment policy hooks to initialize state, read a key, accept or reject
a typed character, predict suggestions, and insert the selected token. EXP-006
implements those hooks with BASIC ROM `POLCAT`, letters and digits,
space-delimited four-word parsing, and a trailing space after every accepted
word. EXP-007 can reuse the complete ten-row editor and edge-corrected popover
while substituting punctuation-aware parsing, five-token context, punctuation
spacing, and the keyboard adapter required while BASIC ROM is hidden.

The learning engine must not depend on CoCo 3 memory banking, GIME video
features, or fast mode. Platform-specific code belongs behind narrow display,
keyboard, timing, and storage interfaces.

Build and verify the full engine:

```sh
make model-test
make coco-bin
make xroar-test
make model-test-exp5
make coco-bin-exp5
make xroar-test-exp5
make model-test-exp6
make xroar-test-exp6
make model-test-exp7
make workbench-test-exp7
make xroar-test-exp7
```

Launch the whole-machine demonstration:

```sh
make xroar
make xroar-exp5
make xroar-exp6
make xroar-exp7
```

The interactive launcher explicitly enables XRoar's stock-rate limiter. The
CoCo screen uses a left-aligned, full-width dark title bar. The epoch count is
black-on-green on the next row. A separate 32-column row displays both context
tokens and the target, such as `# ACORN > ARCHIMEDES`, and is overwritten for
every example. Context is black-on-green; the expected token is green-on-dark.
`#` represents the model's `<END>` boundary token.

After training, the program displays `PRESS ANY KEY` and waits for a keyboard
event. It then preserves `TRAINING COMPLETE`, leaves one blank row, and fills
the remaining twelve rows with inference samples. Each sample starts with a
black-on-green `# # >` seed and shows generated tokens in green-on-dark fields.
A final-column `+` marks a generated sequence wider than the screen without
stopping or altering the underlying inference.
The completed screen remains visible until XRoar is closed. Do not press `F12`
or `Shift+F12` unless you intentionally want maximum-speed emulation.

The wait loop calls the Color BASIC `POLCAT` vector at `$A000`, which returns
only a newly detected keypress. This avoids treating the key used to launch the
program as permission to begin inference and works through the standard CoCo
1, 2, and 3 BASIC interface.

EXP-005 uses the same training engine with a separate 38-token, 380-parameter
fixture. After the post-training pause, it shows six prompt rows with a
completion row beneath each. The CoCo Up (`$5E`) and Down (`$0A`) key codes move
the visible `>` cursor; Enter (`$0D`) runs greedy inference from the selected
two-token context and advances to the next prompt. Previous completions remain
visible.

EXP-007 uses a Mac-trained model with 255 tokens, five context positions,
21 embedding dimensions, and 32,385 signed Q2.2 parameters. Two parameters are
packed into each byte so the 16,193-byte transport image and resident program
both load below `$7F00`. Startup masks interrupts, selects the SAM all-RAM map,
and expands the parameters to signed bytes at `$8000-$FE80`. Its keyboard
adapter briefly restores the ROM map and interrupt environment around `POLCAT`,
then masks interrupts before making the model visible again.
Punctuation is a real token in both the reference and 6809 parsers. Accepted
punctuation attaches to the preceding word and leaves one separator ready for
the next word. `<END>` is also a visible ranked suggestion. Accepting it
removes that pending separator, leaves the sentence unchanged, and displays
`END OF PHRASE` rather than substituting a lower-ranked word or punctuation
mark.

The original two-MUL signed 8×16 routine remains on EXP-004's hot path.
EXP-005's wider training data eventually creates context-vector values outside
signed eight-bit range, so output-weight updates use a three-MUL signed 16×16
low-word routine. The complete products were measured to fit signed 16 bits,
and the direct simulator verifies all 760 trained parameter bytes against the
reference fixture.

The XRoar launcher uses Stacey's local CoCo 1 firmware archive:

```text
~/OneDrive/CoCo/MAME/roms/cocoe.zip
```

It verifies and boots Tandy Color BASIC 1.1 and Extended Color BASIC 1.0, then
loads the same `build/coco-llm.bin` DECB binary intended for CoCo SDC and
FujiNet. Override `COCO_ROM_ARCHIVE` when using another local archive with the
same `bas11.rom` and `extbas10.rom` members.

`make xroar-test` runs XRoar without its speed limiter and proves that the
whole-machine build uses the expected ROM checksums and reaches the finished
training prompt. The direct simulator separately verifies the complete
generation path. These are automated correctness checks, not the command for
watching the demonstration.

The assembly currently embeds its deterministic expected parameter image so
it can stop on a model mismatch before inference. That 580-byte verification
fixture can be omitted from a later size-focused build.
