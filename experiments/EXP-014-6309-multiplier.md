# EXP-014: What one instruction is worth

## Status

**Built and running in the emulator on both CPUs. Physical hardware
outstanding, and it is the measurement that matters.** A standalone CoCo
program runs the same 58,000 multiplications three ways over the model's own
trained parameters and reports what each one cost. All three reach the
checksum the Python reference computes.

The measured result is under [What the machine did](#what-the-machine-did).
The bit-exactness question that could have killed the idea is settled: a MULD
kernel cannot diverge from the engine the CoCo 1 runs. See
[Bit-exactness](#bit-exactness).

```sh
make bench                                # test, then both emulator runs
uv run python tools/cycle_model_6309.py   # the cycle table and the proof
```

The code is standalone in `src/6309/`, sharing no routine with the learning
engine. See its [README](../src/6309/README.md).

## Question

The CoCo 3 on the exhibit table has a Hitachi HD63C09EP in it. That chip has
`MULD`, a signed 16-by-16 multiply producing a 32-bit result, in one
instruction.

The training engine spends most of its time in a signed multiply built from
the 6809's unsigned 8-by-8 `MUL`. How much of the run is that routine, and
what happens to it when the multiply the code wants exists in silicon?

## Hypothesis

*Recorded before the benchmark was built. Left as written.*

Replacing `multiply_s8_s16` with a `MULD` kernel will:

- produce bit-identical parameters, tokens, and parity results after twenty
  epochs, against the same corpus and the same seed;
- reduce the kernel from 16 instructions to 4, and from an average 85.5 cycles
  to 39;
- remove the sign correction entirely rather than making it faster; and
- leave a measured whole-run speedup that is materially smaller than the
  kernel speedup, because the rest of the program does not get faster.

That last clause is the one worth stating in advance. If the block only shows
the kernel number it will overstate what a faster multiplier buys, which is
the opposite of the lesson.

## Why this is a separate experiment

EXP-004, the live training run, is the performance contract: a stock CoCo 1 at
0.895 MHz, a Motorola 6809, no banking, no fast mode. Nothing here changes it.
This experiment adds a second, clearly labelled machine and asks a question the
first machine cannot answer.

## What the multiply costs today

`multiply_s8_s16` in `src/6809/model_forward.asm` forms a signed product from
two unsigned `MUL` instructions, then corrects for having read a negative
multiplier as an unsigned byte. The operands live above the direct page, so
every variable access is extended.

| | Instructions | Cycles |
| --- | ---: | ---: |
| 6809, negative operand | 16 | 93 |
| 6809, positive operand | 13 | 78 |
| 6309 native, either sign | 5 | 43 |

The sign correction is 3 instructions and 15 cycles on the 6809. On the 6309
it is not a faster correction. It is **not there**, because `MULD` is signed.

The 16-by-16 kernel EXP-005, the prompted marketing completions, uses is
starker: three `MUL` instructions and 105 cycles collapse to `muld ,x` plus
`tfr w,d`, 38 cycles.

## What the machine did

58,000 multiplications, 200 passes over the 290 trained parameters, all three
kernels on one CoCo under XRoar. Ticks are the 60 Hz video counter, which
measures wall-clock time whatever the processor is doing.

| Kernel and mode | Ticks | Seconds | Cycles each | Against the first row |
| --- | ---: | ---: | ---: | ---: |
| 6809 kernel, 6809 emulation mode | 521 | 8.68 | 134.0 | 1.00x |
| 6809 kernel, 6309 native mode | 452 | 7.53 | 116.2 | **1.15x** |
| MULD kernel, 6309 native mode | 340 | 5.67 | 87.4 | **1.53x** |

Every row produced checksum `$1E10`, which is what `tools/export_bench_data.py`
computes in Python. A faster kernel with a different sum would be a broken
kernel.

The three rows are the reason the block is worth its slot. Native mode alone
buys 1.15x. The instruction buys the rest. Neither number alone would separate
"the newer chip is faster" from "the newer chip has the operation this
workload wants", and it is the second claim the block is about.

The data sheet predicted the first row within 1.1% with nothing fitted: 85.5
cycles of kernel plus 50 cycles of benchmark loop is 135.5 against 134.0
measured. That is the row the direct simulator and the data sheet both stand
behind. XRoar labels its own 6309 emulation UNVERIFIED, so rows two and three
are corroboration and the physical CoCo 3 is still the authority.

Double speed needs no code and is not in the table. `TIMER` counts video
frames, so `POKE 65497,0` before `EXEC` halves every row and the comparison
stays honest.

## How much of the run is it

A temporary 24-bit counter at the head of `multiply_s8_s16`, read back from
memory after `make model-test`, gives **306,588 calls** across the complete
twenty-epoch run. Against EXP-004's recorded cycle-model projection of roughly
66.7 million cycles, the kernel and its call overhead account for about
**46% of the entire training run**.

So the projection: `MULD` alone is worth about 1.26x on the training run, and
with the CoCo 3's double clock roughly 2.5x against a stock CoCo 1.

Note how much smaller that is than the 1.53x the benchmark measured, and
smaller again than the 1.99x the kernel gets on its own. Three numbers, each
correct about a different thing: the instruction, the loop around it, and the
program around that. The block has to show the shrinkage rather than quote the
biggest one, because the shrinkage is the lesson.

**The training-run figure is still a projection.** Running EXP-004, the live
training run, on both machines and timing it is the measurement, and it has
not been done.

## Bit-exactness

AGENTS.md requires the computational core to be identical across the
reference, the emulator, the CoCo 1 and the CoCo 3. A different multiplier
looks like a threat to that.

It is not. The 6809 kernel already produces the low 16 bits of the true signed
product, which is exactly what `MULD` leaves in `W`. Checked over all
256 x 65,536 = **16,777,216 input pairs, with zero divergence**.

A MULD kernel that takes the low word of `Q` is therefore bit-exact with the
CoCo 1 engine by construction, not by measurement. The existing parity tests
should pass unchanged, and if they do not, the port is wrong.

## Toolchain

| Tool | 6309 support |
| --- | --- |
| lwasm | Yes. 6309 is the default mode, and it took `muld`, `sex`, `tfr w,d` and `ldmd` without complaint. |
| XRoar 1.12.1 | `-machine-cpu 6309`, which XRoar's own help labels **UNVERIFIED**. |
| The direct simulator | **None.** MC6809 only. |

This is the interesting constraint. The direct simulator is where every
bit-exactness claim in this project is settled, and it cannot run a 6309 at
all. XRoar can, but its author does not vouch for the emulation.

So the CoCo 3 on the table is not a convenience here. It is the only
authority. That is unusual for this project and it should be said out loud
during the block.

## Procedure

1. Confirm the board's programming model on the physical machine before
   trusting any of it. The Boomerang E2 is a BoysonTech 2 MiB SRAM board whose
   public documentation is thin. The Disto convention it presumably follows
   puts two extra block-address bits in the existing DAT registers at
   `$FFA0-$FFAF`, giving blocks 0-255, and those extra bits **cannot be read
   back**. Nothing in this experiment needs banking, but the CPU mode does need
   to be established.
2. Enter native mode by setting bit 0 of the MD register, and confirm the
   existing engine still passes its parity tests in 6809 emulation mode first.
3. Run `bench6809.bin` on the CoCo 1 and confirm 521 ticks. If the physical
   machine disagrees with the emulator on the 6809 row, nothing further in
   this experiment can be trusted.
4. Run `bench6309.bin` on the CoCo 3 and compare all three rows against the
   table above. Then run it again after `POKE 65497,0` and confirm the rows
   halve.
5. Only then consider a third named multiply policy in the engine itself,
   beside EXP-004's 8-by-16 and EXP-005's 16-by-16, and time the complete
   twenty-epoch training run on both machines. That converts the projection
   above into a measurement.

## Null result to respect

If the whole-run speedup lands near the kernel speedup, the cycle accounting
above is wrong and the run is more multiply-bound than measured. If it lands
near 1.0x, the multiply is not the bottleneck and this block should be cut
rather than explained away.

If native mode changes any parity result, the port is wrong and the block does
not go in the talk at all.

## Why it earns a slot

The block pays off block 3's arithmetic. That block spends real time on why
the 6809 needs two multiplies and a sign correction. Here, a chip from five
years later just has the instruction, and the correction the audience was
taught to follow evaporates.

The generalization is the reason to run it. Nobody made the CoCo faster at
everything. They made it faster at one operation, which happens to be the
operation this workload spends nearly half its time inside. That is what an
accelerator is, and a GPU is that same decision repeated until it fills a
building.

Placement: immediately after block 3, while the sign fix is still on screen,
and **explicitly droppable**. Block 3 has never been timed. A bonus block
adjacent to the one unknown in the runsheet is the natural pressure valve.
