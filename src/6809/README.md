# 6809 implementation

This folder contains the first complete bit-exact training implementation:

- `model_core.asm` — initialization, forward pass, approximate softmax,
  backpropagation, parameter updates, and sampling;
- `coco_llm.asm` — the writable CoCo program at `$2000`;
- `tests/model_test.asm` — the direct-simulator wrapper.

The learning engine must not depend on CoCo 3 memory banking, GIME video
features, or fast mode. Platform-specific code belongs behind narrow display,
keyboard, timing, and storage interfaces.

Build and verify the full engine:

```sh
make model-test
make coco-bin
make xroar-test
```

Launch the whole-machine demonstration:

```sh
make xroar
```

The interactive launcher explicitly enables XRoar's stock-rate limiter. The
CoCo screen uses a left-aligned, full-width dark title bar. The epoch count is
black-on-green on the next row. A separate 32-column row displays both context
tokens and the target, such as `<END> ACORN > ARCHIMEDES`, and is overwritten
for every example. After training, the program displays
`PRESS ANY KEY` and waits for a keyboard event before generating five names.
The completed screen remains visible until XRoar is closed. Do not press `F12`
or `Shift+F12` unless you intentionally want maximum-speed emulation.

The wait loop calls the Color BASIC `POLCAT` vector at `$A000`, which returns
only a newly detected keypress. This avoids treating the key used to launch the
program as permission to begin inference and works through the standard CoCo
1, 2, and 3 BASIC interface.

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
