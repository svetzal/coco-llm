# Development toolchain

## Decision

Use two levels of 6809 execution during development.

### CPU-level tests

Use:

- **LWASM** from LWTOOLS as the production cross-assembler;
- **gorsat/6809** as a small command-line assembler, simulator, and test runner.

This loop does not boot or emulate a Color Computer. It is suitable for pure
6809 routines such as fixed-point multiplication, saturation, lookup tables,
matrix kernels, the PRNG, forward propagation, and parameter updates.

The simulator supports assertions embedded in assembly comments. A kernel test
can therefore be assembled by LWASM to verify production syntax, then executed
directly by the simulator to verify behaviour.

The simulator is pinned in the `Makefile` to Git revision
`546c8d2efc7d30cecb5afe9bc05e683a4bfbd672`. Install the development tools with:

```sh
brew install lwtools rustup
make tools
```

`make tools` needs `cargo`, because the simulator is a Rust crate installed
from its repository at that revision.

Run both reference and assembly tests with:

```sh
make test
```

The CPU simulator is not cycle-accurate. Its performance report cannot establish
CoCo 1 timing.

### Machine-level tests

Use XRoar when behaviour depends upon the Color Computer rather than only the
6809:

- memory map and ROM interaction;
- VDG or GIME display;
- keyboard handling;
- disk and cassette images;
- CoCo 1 versus CoCo 3 integration;
- debugger-assisted system testing.

XRoar provides CoCo 1, 2, and 3 emulation, disk and cassette images, snapshots,
and a GDB target. It requires the appropriate Tandy ROM images.

The ROMs are not in the repository. The Makefile reads them from a
MAME-style archive named by `COCO_ROM_ARCHIVE` (and `COCO3_ROM_ARCHIVE` for
the CoCo 3), whose default is the author's own copy. The CoCo 1 set:

| Firmware | Archive member | CRC32 |
| --- | --- | --- |
| Tandy Color BASIC 1.1 | `bas11.rom` | `6270955a` |
| Tandy Extended Color BASIC 1.0 | `extbas10.rom` | `6111a086` |

XRoar recognizes both checksums as valid firmware. `make xroar` extracts them
into the ignored build directory and runs the real DECB program in a 32K NTSC
CoCo 1 profile with the stock-rate limiter enabled. Install XRoar with:

```sh
brew install xroar
make xroar
```

`make xroar-test` independently validates both checksums and proves that the
emulated machine reaches the program's finished loop. The direct simulator
remains the automated bit-exact arithmetic test runner and physical hardware
remains the timing authority.

Physical CoCo 1 hardware remains the authority for wall-clock timing and the
final demonstration claim. The CoCo 3 verifies compatibility and provides the
HDMI presentation path.

## Why not use only a full emulator?

A whole-machine emulator adds ROMs, peripherals, startup state, and interactive
UI to every inner-loop test. That realism is valuable late and expensive early.

Most of the learning engine is deterministic arithmetic over memory. Running
those routines directly makes failures smaller, tests faster, and automated
verification straightforward. Machine emulation then tests the narrower layer
where hardware realism matters.

## Sources

- [LWTOOLS manual](https://www.lwtools.ca/manual/manual.html)
- [gorsat/6809 repository](https://github.com/gorsat/6809)
- [XRoar documentation](https://www.6809.org.uk/xroar/doc/xroar.pdf)
