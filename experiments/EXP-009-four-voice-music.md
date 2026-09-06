# EXP-009: Four-voice music on a stock CoCo 1

## Status

**Accepted and frozen** as of 2026-08-01. Judged good enough by ear on XRoar
and VCC after the timing rework, and held stable so that generation work has a
fixed performer to target.

Runnable in XRoar and VCC. The reference synthesizer, the 6809 player, the
cycle budget, the DECB disk image, and bit-exact parity between reference and
assembly all exist and pass. Physical CoCo 1 audio and timing remain
unmeasured.

Frozen means the sample loop, the token format, and the 5679 Hz rate should
not move without a reason recorded here. Anything generated for this player
depends on all three. The open questions below stay open; they are candidates
for a later pass, not pending work.

This experiment exists to support a possible music direction for the model
work. It deliberately builds the *player* first, because a generator is
worthless without something that can perform its output.

## Question

Can a stock CoCo 1 play four-voice music from a single 6-bit DAC, in tune and
without audible timing artefacts, using enough of the machine to leave room
for something else to run between patterns?

## The constraint that determines everything

The CoCo 1 has no timer usable at audio rates.

Its only periodic interrupt fast enough is horizontal sync at 15.734 kHz. A
6809 IRQ costs 19 cycles to enter, because it stacks all twelve bytes of
register state, and 15 more to leave. Against a 56.9-cycle HSYNC period, that
is 60% of the machine before the handler does anything. Adding the ROM vector
jump, the flag-clearing read of `$FF00`, and a divider to use only every Nth
interrupt brings the fixed overhead to 56 of 56.9 cycles — **98%**.

Dividing does not help, because the overhead is paid on every HSYNC including
the ones discarded.

| Divider | Sample rate | Cycles left for the sample |
| ---: | ---: | ---: |
| 2 | 7867 Hz | 1.8 |
| 3 | 5245 Hz | 2.6 |
| 4 | 3934 Hz | 3.5 |

A sample needs about 140. FIRQ would be far cheaper at 10 in and 6 out, but
HSYNC is wired to IRQ; FIRQ comes from the cartridge slot. The CoCo 3's GIME
has a programmable timer, but that is not this machine.

**So the sample clock has to be the instruction stream itself.** The sample
rate *is* the loop's cycle count. This is not a stylistic choice about how to
write CoCo audio; it is forced, and it makes one rule absolute: every path
through the sample loop must cost the same, and anything that runs between
samples must fit between samples.

Both bugs found in this experiment were violations of that rule, and both were
found by ear before they were found by arithmetic.

## Technique

Each voice produces one bit per sample. Voices 0 to 2 add a 16-bit increment
to a 16-bit phase accumulator and take bit 15, so frequency comes entirely
from the increment with full 16-bit precision. Voice 3 is a dedicated noise
channel with no accumulator: a maximal-length 16-bit LFSR is clocked once per
sample and its low bit is the output.

Amplitudes are summed branchlessly. With A zero, `SBCA #0` leaves `$FF` when
carry is set and `$00` when it is clear, so ANDing that mask against a voice's
amplitude adds either the amplitude or nothing without a test:

```asm
                rola                    ; the voice's bit into carry
                lda     #$00
                sbca    #$00            ; $FF if high, $00 if low
                anda    <scaled+n       ; its amplitude, or nothing
                adda    <dac_acc
```

The same trick applies the LFSR tap. Volumes are pre-shifted into PA2-PA7
position, so four voices at full volume sum to 240 and never leave a byte.
There is no multiply, no divide, and no branch.

Percussion needs no envelope generator: a per-tick decrement of the amplitude
gives the kick and snare their shape.

| Measurement | Result |
| --- | ---: |
| Sample loop | 156 cycles, constant |
| Sample rate during playback | 5737 Hz |
| Effective average rate | 5679 Hz |
| Voices | 3 tone + 1 noise |
| Resident image | 988 bytes at `$2000` |
| Increment table | 194 bytes, MIDI notes 12-108 |
| Row data | 12 bytes per row |

The complete player fits a stock 32 KiB CoCo 1 with no all-RAM memory map,
making it simpler to load than EXP-006 or EXP-007.

## Two bugs, both heard before they were calculated

### Variable loop cost, heard as garbling

The first working version let voice 3 be either square or noise, selected per
note. That put a branch in the sample path, and the LFSR tap added two more.
The sample period varied with what the noise generator happened to do:

| Path | Cycles | Instantaneous rate |
| --- | ---: | ---: |
| Voice 3 square | 133 | 6729 Hz |
| Noise, no wrap | 137 | 6533 Hz |
| Noise, wrapped | 152 | 5888 Hz |
| Noise, wrapped and tapped | 165 | 5424 Hz |

A 24% swing in sample period is frequency modulation applied to every voice at
once. It was reported as "a bit garbled and not quite in tune", and the second
half of that was the same cause: the declared rate was an average of something
that never sat still.

The fix was to make voice 3 a dedicated noise channel, as a period sound chip
does, and to apply the tap branchlessly. Same trade, same reason.

### Housekeeping stalls, heard as warble

With the loop constant, the tune still warbled. The suspect was the mix table:
sixteen precomputed voice sums made the sample path cheap, but forced a
199-cycle rebuild whenever a volume changed. With the decay loop that came to
426 cycles, or 3.15 sample periods, at 50 Hz.

This was tested rather than assumed. `steady_tune()` holds a chord with no
decay, so no volume ever changes, the rebuild never runs, and rows are 200
ticks apart. It was reported as indistinguishable from the reference on both
XRoar and VCC, which isolated the stall as the cause while leaving the
oscillators, the DAC path and the loop untouched.

The fix was to delete the mix table rather than to make it cheaper. Masking
each amplitude in branchlessly costs 21 more cycles per sample and removes the
rebuild entirely.

Row processing was then spread one cell per sample, by setting `tick_samples`
to 1 so the tick handler is re-entered on the next sample, and giving back the
borrowed samples afterwards so tick timing stays exact.

| Pause | Original | After | Rate |
| --- | ---: | ---: | ---: |
| Mix rebuild | 3.15 sample periods | removed | 50 Hz |
| Row cells | 6.1 | 0.92 each | 8.3 Hz |
| Decay | included above | 0.79 | 50 Hz |

Every pause between samples is now shorter than the interval it interrupts.

## Verification

`make music-test` runs 200 samples through the real sample loop in the direct
simulator and checks the result against `src/reference/coco_synth.py`: the
three phase accumulators, the LFSR after every clock, and **the byte written
to `$FF20`**. In the simulator that address is ordinary memory, so it still
holds the last value the player wrote, which makes this a check of the actual
hardware output rather than of internal state.

`make music-cycles` enumerates the sample loop instruction by instruction with
its data-sheet timing and derives the sample rate. This is not decoration. An
early estimate of 7300 Hz was 12% high, which would have played the whole tune
nearly two semitones flat; making the arithmetic auditable caught it.

The direct simulator counts instructions rather than cycles, so the instruction
total is used as a cross-check on the hand-enumerated cycle count.

## Unverified

- Physical CoCo 1 audio, timing, and pitch. Everything here is emulator and
  simulator evidence.
- The derived 5679 Hz rate is exact for the sample loop but its amortised
  tick and row term depends on the music's branch mix. Roughly one percent.
- The `$FF01` and `$FF03` multiplexer select combination is taken from
  documentation, not confirmed against hardware. It is the one part of the
  audio path the parity test does not cover.

## Open questions

1. How much of the remaining roughness is zero-order hold and square-wave
   aliasing at 5679 Hz, which are inherent, versus anything still fixable?
2. Every note zeroes its phase accumulator. Does that discontinuity click
   audibly, and is retaining phase across notes better or worse?
3. Is 5679 Hz with four voices the right point, or would three voices at a
   higher rate sound better?
4. What does the loop cost on physical hardware, where video DMA and DRAM
   refresh may not leave the 6809 the clean cycle count the data sheet implies?

## Relationship to the model work

None yet, deliberately. This is a player. Whether a next-token model should
generate tracker patterns for it is a separate question with its own gates,
and the screening test from EXP-008 applies: the context space must be too
large to tabulate, there must be real structure to generalize across, and
there must be no cheap algorithm that is already at least as good.

Tracker data is a natural token stream and pattern reuse is real long-range
structure, which is why the direction is interesting. But EXP-008 closed
because a ninety-byte table beat the model, and nothing here changes the
obligation to check that first.

## Addendum, 2026-09-06: the standalone player was broken

Found while building EXP-015, the faster-clock listening test, whose
emulator runs never reached the end of the tune. On 2026-08-02 the row
hook was handed to the caller so the composer's cursor could run
(`a60e53e`), and the standalone wrapper `coco_music.asm` was never given
one to set. From the end of its first row the player did `jsr [row_hook]`
into whatever the RAM held. The direct-simulator parity test did not see
it because it runs 200 samples of the loop and never a row.

The fix is in the wrapper, which now points the hook at `row_hook_none`
before entering, and the same three lines are in EXP-015's two wrappers.
The sample loop and the 5679 Hz rate are untouched, so the freeze stands:
`build/coco-music.bin` differs from the frozen build only by that entry
stub. `make xroar-test-music` now plays the whole tune to `audio_disable`
under XRoar's CoCo 1, so a row-level regression cannot hide behind the
sample-loop parity again.

### And a second cell it never wrote

Found the same day, building EXP-017, the wavetable voices. `music_start`
reads `ticks_cfg` and applies the default tempo only if the cell is zero,
so a caller can set a tempo first. The standalone wrapper never wrote it
either. The direct simulator zeroes RAM, and XRoar's power-on pattern
happened to hold a zero at that address in this player's layout; the
wavetable player's layout moved the cell onto an `$FF`, and its tune ran
at 255 ticks a row until the emulator gave up. On a real machine the RAM
is whatever it is, so the frozen player's tempo on hardware had been a
coin toss.

Every standalone wrapper now clears `ticks_cfg` beside setting the hook,
and every whole-tune emulator test runs with `--ram-init set`, XRoar's
all-ones power-on pattern, so a cell that is read before it is written
fails on the Mac rather than at the table.
