# 6809 implementation

This folder contains the first complete bit-exact training implementation:

- `model_core.asm` — initialization, forward pass, approximate softmax,
  backpropagation, parameter updates, and sampling;
- `coco_llm.asm` — the writable CoCo program at `$2000`;
- `xroar_boot.asm` — a ROM-less XRoar cartridge bootstrap;
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

The XRoar cartridge needs no Tandy BASIC ROM. It copies the program into RAM,
shows training status on the VDG text screen, checks all final parameters, and
prints five generated names. The resulting `build/coco-llm.bin` is a DECB
binary intended for the later CoCo SDC and FujiNet loading procedure.

`make xroar-test` runs XRoar without its speed limiter and proves that the
whole-machine build reaches the finished program counter.

The assembly currently embeds its deterministic expected parameter image so
the screen can report `BIT EXACT: YES`. That 580-byte teaching and verification
fixture can be omitted from a later size-focused build.
