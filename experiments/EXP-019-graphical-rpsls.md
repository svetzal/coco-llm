# EXP-019: the graphical hand game

## Hypothesis

A stock-clock, 32 KiB CoCo 1 can run a CG6 (128 × 192, four-colour)
Rock, Paper, Scissors, Lizard, Spock game with two 48 × 72 sprite slots,
a brief player-first reveal, persistent scores, and readable key instructions.
The graphical interface can reuse the opponent from EXP-013, the game opponent
that learns, without changing its choices for a fixed seed and throw sequence.

The interface is for play. It does not display predictions or learning tables.
The computer commits its choice before accepting the player's throw.

## Checks

- Compare all 25 throw pairings with the independent reference rules.
- Compare a deterministic session with the existing reference opponent.
- Compare CG6 framebuffer bytes with a reference renderer.
- Exercise all five keys, invalid input, new game, and score saturation.
- Run the executable with real BASIC ROMs in XRoar, including nonzero RAM.
- Inspect the actual emulator display and play through the keyboard.

## Evidence and conclusion

Supported in XRoar 1.12.1 with a 6809, 32 KiB CoCo 1 profile and the real
Color BASIC 1.1 / Extended Color BASIC 1.0 ROMs. Startup RAM was set to ones.
Physical hardware remains untested. Stacey confirmed the game plays correctly.

The final play screen has one numeric win count under each hand. A tie adds
nothing to either score. The counters saturate at 999. This replaced the initial
wins/losses/ties display after user feedback that the screen was confusing.
R starts a new game and clears both scores and the opponent's learning state.

`tools/test_rpsls_graphics.py` passed all 25 pairings, a 2,200-round session
with the same computer choices as the reference opponent, six exact framebuffer
checks, seven invalid keys, score saturation, and restart. The player-first
reveal pause measured 18 emulated video frames (about 0.30 seconds at NTSC).
Scripted routine calls establish these checks; they are not physical keypresses.
The original opponent's existing simulator tests also passed.

Each 48 × 72 sprite is 864 bytes; all five total 4,320 bytes. The framebuffer
is 6,144 bytes at `$0400–$1BFF`, and code starts at `$2000`; the build checks
that code/assets remain below the stack reserve. Each sprite blit copies 72
rows of six 16-bit words: 432 word loads and 432 word stores, plus addressing
and loop control. This is an operation count, not a measured hardware latency.
The executable DECB file is 8,098 bytes, including its load-record framing.

The boot smoke test also exposed an existing XRoar option-order bug:
`-trap-snap` before `-trap` could capture startup. `tools/test_xroar.py` now
puts the overall timeout first, then the PC trap, then its snapshot and exit
actions. The new reusable skill's smoke helper additionally checks known RAM
bytes and passed an unreachable-trap negative control.

## Build and play

- `make rpsls-graphics-bin` builds the executable.
- `make xroar-rpsls-graphics` launches normal-speed play.
- `make xroar-test-rpsls-graphics` checks boot.
- `uv run python tools/test_rpsls_graphics.py` checks state and rendering.
- `make rpsls-graphics-dsk` builds `build/exp019/RPSLS.DSK`.

## Disk delivery

The standard 161,280-byte RS-DOS image contains `RPSLS.BIN` and uses four
of 68 granules. Its file was extracted and compared byte for byte with the
built executable. XRoar then loaded it through Disk Extended Color BASIC 1.1
and reached the expected input screen; all 6,144 framebuffer bytes matched.
This tests the disk path, not just direct binary injection.

On a 32 KiB or larger CoCo 1 with Disk BASIC, mount the disk as drive 0 and enter:

```basic
PCLEAR 1
CLEAR 200,8191
LOADM"RPSLS"
EXEC
```

`PCLEAR 1` matters: the default graphics reservation made `CLEAR 200,8191`
fail with `?OM ERROR` in the disk-load test. The game takes over the display
and RAM after loading. This image is loaded with `LOADM`; it is not an
automatically booting disk. Use the hardware interface's own mounting procedure.

Disk SHA-256:
`097cfbb38f505273b7bf0481da23cb132ca10fac958158fcaab93742a6a8d8b9`.

## Reusable workflow

The personal `coco-game-dev` skill records assembly, CG6 assets, explicit XRoar
launching, meaningful trap checks, RS-DOS packaging, and the tested disk loader.
It treats user-confirmed play as sufficient play-test evidence and keeps
window-control failures separate from game failures.
