# EXP-014, the 6309 multiplier block

A standalone benchmark. It shares no code with the learning engine and nothing
in the engine depends on it. What it does share is the engine's arithmetic and
the engine's numbers: `bench_kernel_6809` is transcribed from
`multiply_s8_s16` in `src/6809/model_forward.asm`, and the values it
multiplies are the 290 parameters the model holds after twenty epochs together
with the context bytes a real forward pass produces.

That matters. A benchmark over invented data would execute the same
instructions and tell you nothing about this workload.

## What it measures

One kernel call is a signed 8-bit multiplicand times a signed 16-bit weight,
which is the operation the forward pass spends most of its time inside. The
program runs 200 passes over the parameter block, 58,000 multiplications, and
accumulates the products into a 16-bit sum.

The 6309 build runs three kernels over the same data:

| Row | What it isolates |
| --- | --- |
| 6809 kernel, 6809 emulation mode | what a stock machine does |
| 6809 kernel, 6309 native mode | what the mode alone is worth |
| MULD kernel, 6309 native mode | what the instruction is worth |

Three rows rather than two, because a single before-and-after cannot separate
a generally faster chip from a chip that has the instruction this workload
wants, and that distinction is the point of the block.

## Why the checksum is there

`tools/export_bench_data.py` computes the sum in Python, with the same 16-bit
wraparound the 6809 performs, and writes it into the generated include as
`BENCH_PASS_SUM`. The program checks every run against it and says on screen
whether it agrees.

A faster kernel that produces a different sum is a broken kernel, and a block
that reported the speed without checking the answer would be worthless.

## Timing

`TIMER` at `$0112` is Color BASIC's tick counter, driven by the 60 Hz video
interrupt. It counts frames, not processor cycles, so it measures the same
wall-clock second whatever speed the processor is running at. A faster CPU has
to show up as fewer ticks. That is also why double speed needs no code: enter
`POKE 65497,0` before `EXEC` and every row halves.

## Build and run

```sh
make bench-test          # the 6809 kernel against the Python checksum
make bench-bin           # three CoCo binaries and a disk image
make bench-xroar-6809    # the stock-machine baseline
make bench-xroar-6309    # all three rows
make bench               # all of it
```

Three binaries, because two of them are insurance:

| Build | Defines | Rows |
| --- | --- | --- |
| `bench6809.bin` | none | the 6809 kernel only |
| `bench6309.bin` | `BENCH_6309`, `BENCH_NATIVE` | all three |
| `bench6309safe.bin` | `BENCH_6309` | MULD without native mode |

Native-mode interrupt stacking is the one thing here that has never run on
real silicon. MULD works in either mode, so the fallback still gets the
comparison the block is about if native mode misbehaves.

They load at **$4000**, not the `$2000` the rest of the project uses. With Disk
BASIC the program area starts near `$2601` and the graphics pages occupy
`$0E00-$2600`, so `$2000` is inside memory BASIC will use. A precaution from
the memory map rather than a fault anyone has reproduced.

For the hardware session see
[EXP-014's session sheet](../../experiments/EXP-014-hardware-session.md).

## What each tool can and cannot do

| Tool | 6309 |
| --- | --- |
| lwasm | Yes. 6309 is its default mode. |
| XRoar 1.12.1 | `-machine-cpu 6309`, which XRoar's own help labels UNVERIFIED. |
| The direct simulator | None. MC6809 only. |

Every bit-exactness claim in this project is normally settled on the direct
simulator, and it cannot run a 6309 at all. So the physical CoCo 3 is the
authority for anything the 6309 does here, which is unusual for this project
and worth saying out loud during the block.

## A register convention, learned the hard way

Nothing passes a 16-bit value in `D` alongside a small number in `A` or `B`.
`B` is the low half of `D` and `A` is the high half, so `ldd value` followed by
`ldb #column` silently replaces half the value with the column. Values travel
in `X`, or the small number is stored before the value is loaded. Two display
routines had this bug and both printed plausible wrong numbers rather than
failing.

## Reading the result

The screen is what a person reads. `bench_trap` is what a test reads: the
program leaves every result in a register there, so `tools/run_bench_xroar.py`
can trap on that address and take all four numbers off a single line of
XRoar's instruction trace. Reading them out of a trap snapshot was tried
first, and the snapshot came back as an empty machine often enough not to be
trusted.
