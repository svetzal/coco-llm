# EXP-015: The faster-clock listening test

## Status

**Built, emulator-checked, awaiting the CoCo 3.** Three builds of the
EXP-009 four-voice player exist and each plays its tune to the end under
XRoar. What they sound like on the physical CoCo 3 through the Commodore
1703 is the experiment, and it has not been run.

Building it found that the standalone player had been silently broken
since 2026-08-02. That is recorded in EXP-009's addendum and fixed; the
fix is in the wrapper, not the frozen loop.

## Question

The EXP-009 player runs at 5,679 samples per second because that is what
its loop costs on a 0.89 MHz 6809. The CoCo 3 on the exhibit table has a
faster clock and a 6309. Does a higher sample rate audibly improve the
sound, and by how much, before anyone spends effort on a 6309 rewrite of
the loop?

The suspicion, recorded before listening: most of the roughness at
5.7 kHz is the square waves' harmonics folding back below a 2.8 kHz
Nyquist ceiling. Doubling the rate should remove most of it; the further
step to 14 kHz should be a smaller gain, and the sound will then be
limited by the one-bit waveform and the 6-bit DAC, not the rate.

## Hypotheses

*Recorded before the machine was heard. Left as written.*

1. **The fast-clock build plays at the same pitch and tempo as the CoCo 1
   build.** The loop is byte-identical; only the clock doubles, so the
   rate doubles exactly and the retuned table cancels it. Any audible
   pitch or tempo difference between `MUSIC09` and `MUSIC2X` falsifies
   this, and would mean the CoCo 3's fast clock is not twice its slow one.
2. **The 6309 native-mode build plays at the same pitch and tempo too.**
   Its rate, 14,405 Hz, is a data-sheet prediction: the loop's
   instructions in the HD6309 native-mode cycle column. A one-percent
   error is seventeen cents and inaudible; a six-percent error is a
   semitone and obvious. If `MUSIC39` is audibly out of tune against
   `MUSIC09`, the native-mode cycle table in `tools/music_cycle_budget.py`
   is wrong, and the tune's length by stopwatch says by how much.
3. **The 11.4 kHz build sounds audibly cleaner than the 5.7 kHz one, and
   the 14.4 kHz build only slightly cleaner again.** Subjective, so the
   record is words and, if possible, a phone recording of each.
4. **Native mode runs the player without fault.** EXP-014, the 6309
   multiplier benchmark, already ran native mode on this silicon with
   interrupts enabled. The player masks them, which is the easier case.

## The builds

| File | Built from | Processor | Clock | Loop | Rate | Samples per tick |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `MUSIC09.BIN` | `src/6809/coco_music.asm` | 6809 | 0.89 MHz | 156 cycles | 5,679 Hz | 114 |
| `MUSIC2X.BIN` | `src/6809/coco_music_fast.asm` | 6809 | 1.79 MHz | 156 cycles | 11,358 Hz | 227 |
| `MUSIC39.BIN` | `src/6309/coco_music_native.asm` | 6309, native mode | 1.79 MHz | 123 cycles | 14,405 Hz | 288 |

The loop is the same instruction stream in all three. Rates include the
amortised tick and row work, 1.6 cycles per sample on the 6809 and 1.26
in native mode, so the three tables differ only in what the machine is
expected to cost. The tune is EXP-009's demo, two passes, 7.7 seconds in
every build.

Two things had to change to make the third build possible, both under
`ifdef` so the CoCo 1 player assembles to the same bytes as before:

- The fast builds write `$FFD9` where the CoCo 1 build writes `$FFD8`, and
  write `$FFD8` again on exit so BASIC gets its clock back.
- A 50 Hz tick at 14,405 Hz is 288 samples, which does not fit the byte
  the 6809 player counts ticks in. The 6309 build keeps the countdown in
  its W register: `DECW` costs 2 cycles against the 6809's 9 for
  `DEC`/`BNE` on a byte in memory, and every write to the count goes
  through one macro that picks the width.

```sh
make exp015              # builds, reference renders, emulator runs
make music-cycles-6309   # the native-mode cycle table and its arithmetic
```

Everything lands in `build/exp015/`: the three `.BIN` files under the
names above, `MUSIC015.DSK` carrying all three, and the reference synth
rendered at each rate as `music-5679.wav`, `music-11358.wav` and
`music-14405.wav`, which is what each build should sound like, to hear on
the Mac before carrying the card over.

## What the emulator did

Each build was run under XRoar to a trap at `audio_disable`, which the
player reaches only after its last row of its last pass:

| Build | XRoar machine | Reached the end |
| --- | --- | --- |
| `MUSIC09.BIN` | CoCo 1, 6809 | yes |
| `MUSIC2X.BIN` | CoCo 3, 6809 | yes |
| `MUSIC39.BIN` | CoCo 3, 6309 | yes |

A trap on the 64th row fetch fired and a trap on the 65th did not, so all
32 rows played twice. This proves the tick machinery works at the new
rates and that `DECW` and `LDMD` do what the 6309 build needs. It says
nothing about pitch: XRoar runs the emulated processor at whatever the
host allows and its 6309 emulation is, in its own words, unverified.
The 6309 row is the one genuinely being tested on the day.

### Heard on the emulator, 2026-09-06

Stacey played `MUSIC39` in XRoar's 6309 CoCo 3 with the rate limiter on,
through the Mac's speakers, and called it a marked improvement over the
CoCo 1 player. Against `MUSIC2X` at 11.4 kHz, the same session, she heard
a distinct further gain from `MUSIC39`: a warmer tone. Warmer is what
less aliasing sounds like; the folded-down harmonics that give the
square waves their edge at a low rate are inharmonic, and thinning them
reads as warmth rather than as brightness.

That is one listener, one emulator, and the machine's DAC as XRoar
models it, so it is a reason to expect hypothesis 3's first half to hold
and its second half, that the step to 14 kHz is small, to fail. If the
1703 agrees, the W-register rewrite of the loop earns its experiment.
The 1703 session below is still the one that decides.

### Heard on the CoCo 3 through the 1703, 2026-09-06

Stacey played the builds on the physical CoCo 3 into the Commodore 1703.
The higher rates were audibly better: brighter, and the drum track in
particular gained from it. Hypothesis 3's first half holds on hardware.

She also heard a warble on the melody voice at a specific rate, about 8
to 10 Hz, and could not tell whether the other voices had it. That is
not a hypothesis this experiment made; it is a finding. The tune's rows
change 8.33 times a second, and EXP-009's timing table records that each
of the five borrowed samples at a row change costs 0.92 of a sample
period, so a sustained note's phase slips by about four sample periods
at every row. EXP-018, the steady sample clock, is the experiment that
tests that explanation by removing the slip.

Pitch and tune length against `MUSIC09` were not recorded; hypotheses 1
and 2 are still open.

## Hardware session

Everything is in `build/exp015/` after `make exp015-bin`. Copy the three
`.BIN` files to the SDC under the names above, or mount `MUSIC015.DSK`.

The player loads at `$2000`. On a disk system that sits inside the
graphics pages BASIC reserves, so move them out of the way first:

```basic
PCLEAR 1
CLEAR 200,&H1FFF
LOADM"MUSIC09"
EXEC
```

Then the same for `MUSIC2X` and `MUSIC39`. There is nothing on the screen
during a tune; the file that was loaded is the label. `MUSIC39` will crash
a 6809, which is expected, not a fault.

Listen through the 1703 with its volume where the tune is comfortable and
leave it there for all three. Play `MUSIC09` first, then `MUSIC2X`, then
`MUSIC39`, then `MUSIC09` again, because the ear anchors on whatever it
heard last.

### What to write down

| Build | Played to the end | Pitch against `MUSIC09` | Tune length by stopwatch | The sound, in words |
| --- | --- | --- | ---: | --- |
| `MUSIC09` | | same | | |
| `MUSIC2X` | | | | |
| `MUSIC39` | | | | |

The stopwatch is the instrument for hypothesis 2. Every build should take
7.7 seconds; a build that is a semitone flat takes 8.2. A phone recording
of each, named for the build, is worth more than the words.

### If something goes wrong

| Symptom | Most likely cause | What to do |
| --- | --- | --- |
| `MUSIC2X` sharp or flat against `MUSIC09` | The fast clock is not exactly twice the slow one. | Record it. This changes EXP-014's double-speed rows as well. |
| `MUSIC39` sharp or flat, `MUSIC2X` in tune | The native-mode cycle table is wrong. | Record the tune length. The ratio to 7.7 seconds is the correction to the 123-cycle loop. |
| `MUSIC39` silent, hung, or resets | Native mode misbehaving in this program, or a 6809 in the socket. | `MUSIC2X` still gives the rate comparison. Record it. |
| Any build stops before the end | The row hook. This was the 2026-08-02 fault and should not recur. | Note which build and roughly when. |
| Screen garbled at the fast clock | Not expected on a CoCo 3. | It would be on a CoCo 1; check which machine is playing. |

## After the session

Add a dated section below with the table filled in, then decide:

- If hypothesis 3 holds and the 11.4 kHz build carries most of the gain,
  the next cycles are better spent on waveform than rate: a table lookup
  per voice for triangles or sines, where the one-bit square is now the
  limit. That is a separate experiment.
- If the 14.4 kHz build is clearly better again, the W-register rewrite of
  the loop (two accumulators held in D and W across the sample) is the
  next step, and it changes the loop, which EXP-009 froze.
- If hypothesis 2 fails, fix the cycle table before either.

Nothing goes on a slide until the table above is filled in.

## Relationship to the performance contract

EXP-004, the live training run, is the contract: a stock CoCo 1 at
0.89 MHz. Nothing here touches it. The CoCo 1 build is byte-for-byte the
EXP-009 player plus the hook fix; the two faster builds are labelled
CoCo 3 options, the way EXP-014's benchmark is, and never a substitute for
the CoCo 1 playing its own tune.
