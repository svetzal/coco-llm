# EXP-018: The steady sample clock

## Status

**Supported on the CoCo 3, 2026-09-06.** The warble is gone and the
steady build is preferred; see the dated section below. Built, bit-exact
against its reference, emulator-checked. Two builds, one for each machine, play their tune
to the end under XRoar with hostile RAM, and the 6809 loop agrees with the
reference on every phase, the noise register and the DAC byte.

## Question

On 2026-09-06 Stacey heard a warble on the melody voice through the 1703,
at about 8 to 10 Hz, on the EXP-015 builds. The demo tune's rows change
8.33 times a second. EXP-009's timing table records that a row change
borrows five samples in a row and stretches each by 0.92 of a sample
period, which it accepted as the residual after spreading the work out.
A sustained note's phase therefore slips by about four periods at every
row: a pitch hiccup at the row rate, which is what a warble at 8 Hz is.

Is that the cause? And what does it cost to remove it?

## Hypotheses

*Recorded before the machine was heard. Left as written.*

1. **A player whose every sample costs the same number of cycles has no
   warble.** If `STEADY39` still warbles on the 1703 at the row rate, the
   explanation above is wrong and something else in the signal path is
   modulating the melody voice.
2. **The price is sample rate, about a fifth.** The event path costs 39
   cycles on the 6809 and the idle path is padded to match, so the loop
   is 195 cycles against 156: 4,590 Hz on the CoCo 1, 11,188 Hz on the
   6309 at the fast clock. Falsified if either build is audibly out of
   tune, or if the tune's length by stopwatch is not 7.7 seconds.
3. **Steady at 11.2 kHz is preferred to warbling at 14.4 kHz.** The
   comparison is `MUSIC39` against `STEADY39` on the same machine. This
   is the one that matters, and it is a judgement: if the rate loss is
   heard as the greater loss, the trade goes the other way and a lighter
   version of the same idea is the next step.

## What changed

The player keeps EXP-009's sample loop and loses everything between
samples. The tune is compiled on the Mac into a stream of events, each a
wait in samples followed by one byte and the direct-page offset to store
it at. The loop's tail counts the wait down; when it reaches zero, the
event path stores the byte, reads the next wait and checks for the end,
and when it does not, an idle path of `BRN` instructions costs exactly
the same:

```asm
                dec     <tick_samples   ; 6809 6   6309 5
                bne     idle            ;      3        3
                ldb     ,x+             ;      6        5   the offset,
                lda     ,x+             ;      6        5   the byte,
                sta     b,y             ;      5        5   stored in the page,
                lda     ,x+             ;      6        5   and the next wait
                sta     <tick_samples   ;      4        3
                tst     <finished       ;      6        5
                bne     play_done       ;      3        3
                bra     sample_loop     ;      3        3   = 39 / 34 after bne
idle            ...twelve BRN, or ten BRN and a NOP in native mode...
                bra     sample_loop     ;                   = 39 / 34 after bne
```

X holds the stream and Y the direct page for the whole tune. The CoCo
never fetches a row, applies a cell or decays a volume; the exporter did
that, with the reference's own tick logic, and emitted the resulting
bytes: five writes for a note, one for a decay step, one to silence a
voice. Within a tick the writes land one per sample after the tick's
first sample, so the first sample of every tick is on the old state, as
in the other players. A wait longer than 255 samples is split with a
filler event that writes to a spare cell.

The reference, `src/reference/steady_synth.py`, replays the same bytes
against the same page layout and produces the stream the CoCo produces,
event for event. The demo tune compiles to 673 events, 2,020 bytes.

| File | Built from | Processor | Loop | Rate | Samples per tick |
| --- | --- | --- | ---: | ---: | ---: |
| `STEADY09.BIN` | `src/6809/coco_steady.asm` | 6809, 0.89 MHz | 195 cycles | 4,590 Hz | 92 |
| `STEADY39.BIN` | `src/6309/coco_steady_native.asm` | 6309 native, 1.79 MHz | 160 cycles | 11,188 Hz | 224 |

Nothing is amortised in those rates. That is new: every earlier player's
rate carried a one-to-two cycle estimate for the tick and row work, and
this one's is the loop's cycle count exactly, which also makes it the
sharpest test yet of the cycle tables.

```sh
make exp018                        # streams, builds, parity, renders, emulator runs
make music-cycles PLAYER=steady    # the loop, and the padding each processor needs
make xroar-steady39                # hear it in XRoar's CoCo 3
```

Everything lands in `build/exp018/`: the two `.BIN` files, `STEADY18.DSK`
carrying both, and the reference rendered at each rate.

## What the reference and the emulator did

`make steady-test` runs 200 samples of the same four-voice configuration
every player's parity test uses through the real loop in the direct
simulator, with a two-event stream: a wait of 200, then the event that
ends the tune. Every phase accumulator, the LFSR and the final DAC byte
match, and the DAC byte is `$64`, the byte EXP-009's own test expects,
so the loop is the old loop. The test also checks the assembled
direct-page offsets against the ones the stream is compiled for.

Under XRoar, with RAM set to all ones at power-on, both builds reach
`audio_disable` after the last event of the last pass.

XRoar's 6809 is cycle-accurate enough that the warble should be audible
in it too, with the rate limiter on, on `MUSIC09` against `STEADY09`. That
is worth a listen on the Mac before the card goes over, but the 1703 is
the instrument.

### Heard on the CoCo 3 through the 1703, 2026-09-06

Stacey played `STEADY39` against `MUSIC39` on the physical CoCo 3 and
called it much better. The warble on the melody voice is gone, so
hypothesis 1 holds: the row-change stall EXP-009 accepted was the cause.
Her preference settles hypothesis 3 the same way: a steady clock at
11.2 kHz beats a moving one at 14.4 kHz, and the rate it cost was worth
it. The timing was perfect: the tune's length was as predicted, so
hypothesis 2 holds and, since nothing in this build's rate is amortised,
the HD6309 native-mode cycle table in `tools/music_cycle_budget.py` is
right to within a stopwatch. The CoCo 1 pair was not recorded.

The sample clock is now the thing to protect. Anything that runs between
samples must cost exactly what not running it costs, and the cycle model
is the only instrument on the Mac that checks it.

## Hardware session

Copy the two `.BIN` files to the SDC, or mount `STEADY18.DSK`. The player
loads at `$2000`:

```basic
PCLEAR 1
CLEAR 200,&H1FFF
LOADM"STEADY39"
EXEC
```

`STEADY09` runs on either machine. `STEADY39` needs the 6309.

The pair for hypothesis 1 is `MUSIC39` then `STEADY39`, twice, listening
to the melody voice. The pair for hypothesis 3 is the same pair, listening
to everything. Then on the CoCo 1, `MUSIC09` then `STEADY09`, the same two
questions at the low rate.

### What to write down

| Build | Machine | Played to the end | Warble on the melody | Pitch against `MUSIC09` | Length by stopwatch | Preferred to the `MUSIC` build? |
| --- | --- | --- | --- | --- | ---: | --- |
| `STEADY39` | CoCo 3 | | | | | |
| `STEADY09` | CoCo 1 | | | | | |

### If something goes wrong

| Symptom | Most likely cause | What to do |
| --- | --- | --- |
| The warble is still there | The row stall was not the cause. | Record it; the next suspect is the 50 Hz decay staircase on the amplitude, which is in the tune, not the clock. |
| Out of tune, or not 7.7 seconds | A cycle count in the tail is wrong; nothing here is amortised, so the rate is only as right as the table. | The length ratio to 7.7 seconds is the correction. |
| A click once per tune | The pass boundary: the state resets between passes. | Expected; it is one event in 7.7 seconds. |
| Stops early | An event landing on the wrong cell. | The parity test checks the layout; note the time it stops. |

## After the session

If hypotheses 1 and 3 hold, the steady loop is the player, and the
question becomes how much of the rate to buy back. Two ways, in order of
cost: shrink the event path (a two-byte event with the wait carried
separately saves about eight cycles), or drop the padding and accept an
event path that is 30 cycles longer than idle, which is a fifth of the
old stall and may be inaudible; that is a different experiment because it
gives up the property this one is testing.

The composer in EXP-010 writes rows at run time and would need the
compiler on the CoCo to use this player. That is a real cost and is not
paid here.

## Relationship to the performance contract

Nothing here touches EXP-004, the live training run. The CoCo 1 build is
a stock machine at its own clock; the 6309 build is a labelled CoCo 3
option, like EXP-014's benchmark and EXP-015's.
