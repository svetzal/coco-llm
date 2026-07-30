# EXP-004: Complete 6809 training

## Question

Can the complete fixed-point token model train and generate names in 6809
assembly while remaining bit-exact with the Python reference and plausibly
finishing inside the three-minute CoCo 1 demonstration budget?

## Hypothesis

A readable first port will fit comfortably in 32K. Replacing a bit-at-a-time
signed multiply with a two-`MUL` low-word kernel will bring the 20-epoch run
below the three-minute cycle budget without changing any trained parameter.

## Controlled configuration

- MC6809 instruction set
- 29-token vocabulary
- two-token context
- three-value positional embeddings
- 290 signed Q4.12 master parameters
- 58 online training examples
- 20 epochs and 1,160 total parameter updates
- XorShift16 seed 6809
- the EXP-002 fixed-point softmax and update rules

Python generates the corpus, lookup table, token table, and expected final
parameter image. The assembly implementation initializes its own parameters,
performs every training update, generates its own samples, and then compares
all 580 trained parameter bytes with that expected image.

## Procedure

```sh
make model-test
make coco-bin
make xroar-test
make xroar
```

`make model-test` assembles the production engine with LWASM, runs the resulting
machine code in the direct 6809 simulator, and checks parameter and generation
fixtures. `make xroar-test` proves that a whole-machine CoCo 1 emulation reaches
the post-training keyboard prompt. `make xroar` loads the same DECB program for
interactive inspection and waits for a key before inference.

The XRoar path uses Tandy Color BASIC 1.1 and Extended Color BASIC 1.0 from
Stacey's local `cocoe.zip` MAME archive. XRoar recognizes their respective
CRC32 values, `6270955a` and `6111a086`, as valid firmware. It loads the same
DECB binary intended for CoCo SDC or FujiNet.

## Evidence

### Correctness

The direct simulator passes:

- every one of the 580 final parameter bytes;
- the complete reference parameter checksum represented by that byte image;
- the expected first token of each of the first five generated names.

The first five generated names begin:

```text
COMMODORE
TANDY
COMMODORE
TANDY
COMMODORE
```

matching the integer reference run.

### Size

| Artifact | Size |
| --- | ---: |
| CoCo DECB executable | 2,886 bytes |
| Writable RAM image including work buffers | 3,684 bytes |
| Trainable parameters | 580 bytes |

The writable image occupies `$2000` through `$2E63`, well inside
a 32K CoCo 1.

### Performance

The initial bit-at-a-time signed multiplication routine executed about
38.6 million instructions. The two-`MUL` kernel reduced the same bit-exact run
to 15,824,366 instructions with the epoch and generation display. Showing the
current training pair for every example brings the interactive run to
16,010,640 instructions, excluding the human-length pause.

The direct simulator reports an effective cycle rate which, combined with its
wall time, implies approximately 65.3 million emulated 6809 cycles. At the
CoCo 1's approximate 0.895 MHz clock, that projects to about 73 seconds.

This is a cycle-model projection, not a physical-hardware measurement. XRoar
successfully boots the real CoCo 1 ROM pair, loads the DECB binary, and reaches
the post-training keyboard prompt. The direct simulator verifies the subsequent
generation path. Automated headless runs on this Mac do not provide a
trustworthy stock-rate wall clock. Physical CoCo 1 timing remains the authority.

The interactive XRoar build enables its rate limiter and visibly advances an
epoch counter from 1 through 20. A fixed-width field beside the count cycles
through all 58 examples as `context > expected token`; it is overwritten in
place rather than scrolling. The normal-text training row sits below a
full-width inverse title bar. After its internal model check, the program
pauses at `PRESS ANY KEY`; a keyboard event starts inference and prints five
generated names before leaving the completed screen displayed.

### Multiply range

Instrumentation of the exact 20-epoch reference run found:

| Quantity | Maximum absolute value |
| --- | ---: |
| Context-vector component | 46 |
| Unsaturated logit accumulator | 3,148 |
| Context-error component | 166 |
| Error × context product | 11,408 |

Those measured bounds support the optimized kernel's use of the exact low
16-bit signed product for this fixed demonstration corpus.

## Conclusion

Supported.

The complete training and generation path now runs in 6809 assembly and is
bit-exact with the integer reference for the controlled corpus. Its projected
stock-clock runtime is comfortably inside three minutes and likely near
73 seconds.

The next evidence step is to inspect the on-screen XRoar run interactively, then
spot-check correctness and timing on the physical CoCo 1 and CoCo 3.
