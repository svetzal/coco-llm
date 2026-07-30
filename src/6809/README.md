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
CoCo screen shows an epoch counter from 1 through 20. Beside it, a fixed-width
field displays the latest training pair as `context > expected token`, such as
`ACORN > ARCHIMEDES`, and is overwritten for every example. The program then
reports the final bit-exact check and displays each of five generated names.
The completed screen remains visible until XRoar is closed. Do not press `F12`
or `Shift+F12` unless you intentionally want maximum-speed emulation.

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
program counter. It is an automated correctness check, not the command for
watching the demonstration.

The assembly currently embeds its deterministic expected parameter image so
the screen can report `BIT EXACT: YES`. That 580-byte teaching and verification
fixture can be omitted from a later size-focused build.
