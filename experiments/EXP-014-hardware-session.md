# EXP-014, the 6309 multiplier benchmark: hardware session

One page. Everything needed to run the benchmark on the real machines and
write down what happened. The emulator numbers are in
[EXP-014](EXP-014-6309-multiplier.md); this sheet exists to confirm or refute
them.

## What to take with you

Everything is in `build/bench6309/` after `make bench-bin`.

**Take the three `.BIN` files.** They are ordinary DECB binaries, which is what
the CoCo SDC and FujiNet both load, and they are the artifacts that have
actually been run end to end. `BENCH309.DSK` is there as a convenience and
carries a caveat, [below](#about-the-disk-image).

| File | Machine | Rows | Notes |
| --- | --- | --- | --- |
| `BENCH09.BIN` | CoCo 1, or CoCo 3 | 1 | Plain 6809. The baseline. |
| `BENCH39.BIN` | CoCo 3 with 6309 | 3 | Enters native mode. **Run this one.** |
| `BENCH39S.BIN` | CoCo 3 with 6309 | 2 | MULD without native mode. Fallback. |

`BENCH39.BIN` will crash a 6809. That is expected, not a fault.

All three load at **$4000**, above Disk BASIC's buffers and above the start of
BASIC's program area. The rest of the project loads at `$2000`, which is inside
that region on a disk system; if these run and the other experiments do not,
that is the difference to look at.

## About the disk image

`BENCH309.DSK` is a standard 35-track RS-DOS image and XRoar reads its
geometry and its directory: a `LOADM` of a name that is not on it returns
`?FILE NOT FOUND` rather than failing, which means Disk BASIC parsed the
directory and the granule table this tool wrote.

**A full load out of it was never completed in the emulator.** Neither was
`DIR`, on a disk that Disk BASIC had just formatted for itself, so the rig is
the suspect rather than the image. It is offered as a convenience and not as a
verified artifact. If it does not work, use the `.BIN` files, which have been
run.

## Running it

```
CLEAR 200,&H3FFF
LOADM"BENCH39"
EXEC
```

The `CLEAR` keeps BASIC's string space below the program. Skipping it will
probably work and costs nothing to type.

Each row appears as it finishes and the run takes about nine seconds per row,
so the screen fills over roughly half a minute. When the last line reads
`SUM MATCHES THE REFERENCE`, every kernel agreed with the arithmetic the Mac
computed and the timings are trustworthy.

For double speed, before `EXEC`:

```
POKE 65497,0
```

No rebuild. `TIMER` counts video frames, so every row should roughly halve and
the comparison between rows stays honest.

## What to write down

Copy the ticks and the sum from each row. Ticks are the number that matters,
seconds are 60 ticks each.

| Run | Machine | Speed | Rows to record |
| --- | --- | --- | --- |
| 1 | CoCo 1 | normal | `BENCH09` |
| 2 | CoCo 3 | normal | `BENCH39`, all three |
| 3 | CoCo 3 | `POKE 65497,0` | `BENCH39`, all three |

Three runs. The first two are the experiment; the third is the one Stacey
actually wants to see.

## What the emulator predicts

If the machine agrees with these, the block's numbers are settled. XRoar calls
its own 6309 emulation UNVERIFIED, so rows two and three are the ones genuinely
being tested.

`BENCH39.BIN`:

| Row | Expected ticks | Seconds |
| --- | ---: | ---: |
| 6809 kernel, 6809 mode | 521 | 8.68 |
| 6809 kernel, native mode | 452 | 7.53 |
| MULD kernel, native mode | 340 | 5.67 |

At double speed, roughly 261 / 226 / 170.

`BENCH39S.BIN`, the fallback:

| Row | Expected ticks | Seconds |
| --- | ---: | ---: |
| 6809 kernel, 6809 mode | 521 | 8.68 |
| MULD kernel, 6809 mode | 388 | 6.47 |

`BENCH09.BIN` on the CoCo 1: 521 ticks, the same as the first row above. If the
CoCo 1 and the CoCo 3 disagree on that number, say so before anything else.

Every row must show sum `$1E10`.

## If something goes wrong

| Symptom | Most likely cause | What to do |
| --- | --- | --- |
| `SUM IS WRONG` on any row | The kernel is not computing what the reference computes. | Record which row, and its sum. This is a real result and more interesting than the timings. |
| Hangs or resets after the second row starts | Native-mode interrupt stacking, the one thing here never run on real silicon. | Run `BENCH39S` instead. It uses MULD without native mode and still gives the comparison. |
| All rows show 0 ticks | `TIMER` is not at `$0112` on this ROM, or interrupts are masked. | Time it with a stopwatch and record that instead. |
| `?FC ERROR` or an immediate crash on a CoCo 1 | `BENCH39` was loaded rather than `BENCH09`. | Load `BENCH09`. |
| Screen is garbled at double speed | Expected on a CoCo 1, which cannot display in fast mode. | Only use `POKE 65497,0` on the CoCo 3. |

## After the session

Add a dated section to [EXP-014](EXP-014-6309-multiplier.md) under
**What the machine did** with the measured ticks beside the emulator's. If the
machine disagrees with the emulator on the first row, nothing else in the
experiment can be trusted and that is the finding.

Nothing goes on a slide until this sheet is filled in.
