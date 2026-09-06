# EXP-017: The wavetable voices

## Status

**Built, bit-exact against its reference, emulator-checked, awaiting the
CoCo 3 and the 1703.** Four builds exist and play their tune to the end
under XRoar with hostile RAM. The reference and the 6809 agree on every
phase, the noise register and the DAC byte after 200 samples, and a
square-table build reproduces EXP-009's player exactly.

Building it found a second latent fault in the frozen player, recorded in
EXP-009's addendum: the tempo cell was read before anything wrote it.

## Question

EXP-016, the register-resident loop, ended with an observation: half of
what a tone voice costs is the mask that turns bit 15 of its phase into a
byte of amplitude, and a table lookup on the phase's high byte costs the
same and returns any amplitude curve at all. So: at the rate EXP-015's
builds already run, does replacing the one-bit square with a triangle or
a sine sound better, and does it cost anything?

## Hypotheses

*Recorded before the machine was heard. Left as written.*

1. **The lookup costs the same as the mask.** The 6809 loop is 153 cycles
   against EXP-009's 156, so the CoCo 1 build runs at 5,789 Hz; the 6309
   native build stays at 123 cycles and 14,402 Hz. Falsified if any build
   is audibly out of tune, or if a cell or a decay can be heard as a
   stall.
2. **The square-table build is bit-identical to EXP-009's player.** The
   table for volume v holds v wherever bit 15 would be set, so the same
   configuration must give the same DAC byte. Falsified by the parity
   test; a table player that cannot reproduce the old one is not a fair
   comparison.
3. **The triangle sounds rounder and warmer than the square at the same
   rate, on the CoCo 1 as much as on the 6309.** This is the one that
   matters. Subjective, so the record is words and a recording.
4. **The sine is a smaller step again from the triangle.** A triangle's
   harmonics fall off as one over the square; a sine has none. Through a
   6-bit DAC and a monitor speaker the difference may not survive.

## What changed

Each tone voice keeps its 16-bit phase accumulator and loses its mask.
The voice's volume selects one of sixteen 256-byte pages of a waveform,
and the accumulator's high byte indexes the page. The page number sits in
memory immediately before the phase, so one `LDX` on it reads
page:phase_hi, which is the sample's address, and the lookup is one
`LDA ,X`:

```asm
                ldd     <vstate+7       ; phase
                addd    <incrs+4
                std     <vstate+7
                ldx     <vstate+6       ; page:phase_hi is the sample's address
                lda     ,x
                adda    <dac_acc
                sta     <dac_acc
```

That is 33 cycles on the 6809 against the mask's 34, and 27 in 6309
native mode against 27. The table is sixteen volumes by 256 samples,
4 KiB, generated from the same function the reference reads, so the CoCo
and the model see the same bytes. Values are the reference's 0 to 15
times four, the DAC's PA2-PA7 units; four voices at full volume sum to
240 as before. The noise voice is unchanged.

Because a decay now also rewrites a page number, and the whole decay pass
would no longer fit in one sample period, the tick's four decays are
applied one per sample, the way the row's cells already were. The
reference's `render` follows that timeline exactly: one sample on the old
state, then one after each cell or decay, then the rest of the tick. The
EXP-009 reference applied rows and ticks atomically; its parity was of
the sample loop only, and so is this one's, but the rendered WAVs here
are the player's own timeline.

| File | Built from | Processor | Shape | Rate | Samples per tick |
| --- | --- | --- | --- | ---: | ---: |
| `WAVE09.BIN` | `src/6809/coco_wave.asm` | 6809, 0.89 MHz | triangle | 5,789 Hz | 116 |
| `WAVE2X.BIN` | `src/6809/coco_wave_fast.asm` | 6809, 1.79 MHz | triangle | 11,578 Hz | 232 |
| `WAVE39.BIN` | `src/6309/coco_wave_native.asm` | 6309 native, 1.79 MHz | triangle | 14,402 Hz | 288 |
| `SINE39.BIN` | `src/6309/coco_wave_native.asm` | 6309 native, 1.79 MHz | sine | 14,402 Hz | 288 |

```sh
make exp017                      # tables, builds, parity, renders, emulator runs
make music-cycles PLAYER=wave    # the loop, instruction by instruction
make xroar-wave39                # hear the triangle build in XRoar's CoCo 3
make xroar-sine39                # the sine
```

Everything lands in `build/exp017/`: the four `.BIN` files, `WAVE017.DSK`
carrying all four, and the reference rendered on the player's timeline as
`wave-triangle-5789.wav`, `wave-triangle-14402.wav`, `wave-sine-14402.wav`
and, for comparison, `wave-square-14402.wav`.

## What the reference and the emulator did

`make wave-test` runs 200 samples of a fixed four-voice configuration
through the real loop in the direct simulator, for the triangle build and
for a square-table build. Every phase accumulator, the LFSR and the final
DAC byte match `src/reference/wave_synth.py`. The square build's DAC byte
is `$64`, which is the byte EXP-009's own parity test expects from the
same configuration, so hypothesis 2 holds: the table player contains the
old player.

Under XRoar, with RAM set to all ones at power-on, each build reaches
`audio_disable`, which the player only reaches after the last row of its
last pass:

| Build | XRoar machine | Reached the end |
| --- | --- | --- |
| `WAVE09.BIN` | CoCo 1, 6809 | yes |
| `WAVE2X.BIN` | CoCo 3, 6809 | yes |
| `WAVE39.BIN` | CoCo 3, 6309 | yes |
| `SINE39.BIN` | CoCo 3, 6309 | yes |

The cost of a cell and of one voice's decay between samples is estimated
from the listing, not measured: a cell is near one sample period on the
6809, which is the rule's edge, and comfortably under it in native mode.
A stall would be audible as a click at row boundaries. Listen for it.

## Hardware session

Copy the four `.BIN` files to the SDC, or mount `WAVE017.DSK`. The player
loads at `$2000`, so:

```basic
PCLEAR 1
CLEAR 200,&H1FFF
LOADM"WAVE39"
EXEC
```

`WAVE09` runs on either machine and is the one to play on the CoCo 1.
`WAVE2X` needs a CoCo 3; `WAVE39` and `SINE39` need the 6309.

For hypothesis 3, the pair that isolates the waveform is `MUSIC39` from
EXP-015 against `WAVE39`: same machine, same rate within three hertz,
square against triangle. Play them back to back, twice. Then `SINE39`
for hypothesis 4, and `WAVE09` on the CoCo 1 to hear whether the gain
survives the low rate.

### What to write down

| Build | Machine | Played to the end | Pitch against `MUSIC09` | Clicks at row changes | The sound, in words |
| --- | --- | --- | --- | --- | --- |
| `WAVE09` | CoCo 1 | | | | |
| `WAVE2X` | CoCo 3 | | | | |
| `WAVE39` | CoCo 3 | | | | |
| `SINE39` | CoCo 3 | | | | |

### If something goes wrong

| Symptom | Most likely cause | What to do |
| --- | --- | --- |
| A click at every row change | A cell overrunning its sample period on the 6809. | Note which build. Native mode has the headroom; the 6809 cell would need trimming. |
| Out of tune against `MUSIC09` | The 153-cycle loop count is wrong. | Time the tune; the ratio to 7.7 seconds is the correction. |
| Silent, but the tune's length passes | The table page is wrong: every voice reading page zero. | Record it; the parity test would have to be wrong too. |
| Stops before the end | An uninitialised cell the hostile-RAM test did not reach. | Note when. |

## After the session

Fill in the table and decide which waveform the CoCo 1 player should
carry. If the triangle wins on the CoCo 1, EXP-009's freeze has a reason
recorded here to end: the wavetable loop is the same rate, one cycle
cheaper, and the composer of EXP-010 could perform through it unchanged,
since it reads the same twelve bytes per row.

## Relationship to the performance contract

Nothing here touches EXP-004, the live training run. The CoCo 1 build is
a stock machine at its own clock; the three faster builds are labelled
CoCo 3 options, like EXP-014's benchmark and EXP-015's.
