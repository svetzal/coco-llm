# EXP-016: The register-resident 6309 loop

## Status

**Rejected before building, 2026-09-06.** The cycle arithmetic says a
rewrite of the sample loop around the 6309's extra registers buys about
five percent, which is a rate change nobody will hear. Recorded so the
idea is not re-had, and because working it out found the direction that
became EXP-017, the wavetable voices.

## Question

EXP-015, the faster-clock listening test, showed on the emulator that
sample rate is audible: 14.4 kHz sounded warmer than 11.4 kHz. Its 6309
build runs EXP-009's instruction stream unchanged in native mode, at 123
cycles a sample. The 6309 has registers the 6809 does not: W, with its own
16-bit add and shifts; E and F, its halves; and register-to-register
arithmetic. Can a loop written for those registers cost materially fewer
than 123 cycles while producing the same DAC bytes?

## Hypothesis

*Recorded before the arithmetic. Left as written.*

Holding two of the three phase accumulators in D and W across the whole
sample, so they are never loaded or stored, removes at least fifteen
percent of the loop. The ear test that follows would then be the same
one as EXP-015's, one step further up.

## The arithmetic

Every figure is the HD6309 native-mode column of its data sheet. Where a
count is uncertain the estimate is generous to the rewrite, so a mistake
would make the rewrite look better than it is, not worse. The current
loop is the baseline:

| Piece | Cycles | Notes |
| --- | ---: | --- |
| Noise voice | 36 | LFSR shift, tap, output bit, mask, first sum |
| Tone voice, in memory | 27 | `LDD`/`ADDD`/`STD` 13, mask and sum 14 |
| Three tone voices, last one to the DAC | 78 | |
| Output `STA` extended | 4 | |
| Countdown `DECW`/`BNE` | 5 | W holds the tick count |
| **Loop** | **123** | 14,405 Hz at 1.79 MHz |

The mask, `ROLA` / `LDA #0` / `SBCA #0` / `ANDA` / `ADDA` / `STA`, needs
A, so D is scratch in every voice and cannot hold a phase. That leaves W
for exactly one resident value, and the candidates compete for it:

| Rewrite | What W holds | Saves | Costs | Loop |
| --- | --- | ---: | ---: | ---: |
| A. LFSR in W | the noise register | 9 (`LSRW`, `SBCA`, `EORR` replace two memory shifts and stores) | 3 (countdown moves to `LEAY -1,Y`) | 117 |
| B. One phase in W | voice 0's accumulator | 9 (`ADDW`, `SEXW` replace load, add, store and mask) | 3 (same countdown) | 117 |
| C. DAC sum in E | the running sum | 8 (`ADDR A,E` replaces `ADDA`/`STA` in four voices) | 3 (countdown) + 2 (`TFR`, `STE`) | 125 |
| A and B together | | | | impossible, both need W |

A and B each reach 117 cycles, 15.3 kHz against 14.4: six percent, well
under the fifteen the hypothesis needed and under what EXP-015 found
audible between 11.4 and 14.4 kHz. C is slower than the loop it replaces.
Holding a phase in X or Y instead is worse still: `LEAX D,X` costs more
than the load, add and store it would replace, and X has no way to hand
bit 15 to the carry.

The one restructuring that goes further is not about registers. Gathering
the four voice bits into an index and reading their sum from a
sixteen-entry table, the design EXP-009 rejected, would land near 105
cycles. EXP-009 rejected it because rebuilding the table when a volume
changes stalled the DAC for three sample periods fifty times a second, and
that is still true; the fix would be a rolling rebuild of one entry per
sample, which changes what the reference has to model. That is a possible
later experiment. It is not this one.

## Conclusion

Refuted by arithmetic: the best register-resident rewrite is 117 cycles,
a six-percent gain, against a hypothesis of fifteen. Not built.

What the exercise did show is where the loop's cycles go. Thirteen of a
tone voice's 27 are the phase update, which nothing can shrink; fourteen
are the mask, and the mask exists only to turn one bit into a byte of
amplitude. A table lookup indexed by the phase's high byte turns the
whole byte into an amplitude for the same fourteen cycles on the 6809
and one fewer on the 6309, and the amplitude can then follow any curve
at all. That is EXP-017, the wavetable voices: the same rate, and a
triangle or a sine where there was a square.
