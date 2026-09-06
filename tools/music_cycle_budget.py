#!/usr/bin/env python3
"""Derive the player's sample rate from documented 6809 instruction timings.

The 6809 has no cache and no pipeline, so the sample loop's cost is exactly the
sum of its instruction timings. The direct simulator counts instructions rather
than cycles, so this enumerates the loop instruction by instruction and shows
its arithmetic, and the instruction total is cross-checked against what the
simulator actually executed.

The resulting rate is what tools/export_tune.py must build the increment table
for. Get it wrong and every note is flat or sharp by the same ratio.

The sample-loop figure is exact. The amortised tick and row term is not: it
averages build_mix, next_tick, and apply_cell over the tune, and its branch
mix depends on the music. It is accurate to roughly one percent, which is
about seventeen cents of pitch error and inaudible here. Confirming the rate
on physical hardware remains outstanding.
"""

from __future__ import annotations

import argparse

COCO1_CLOCK = 895000
COCO3_FAST_CLOCK = 2 * COCO1_CLOCK

# (mnemonic, addressing mode, cycles) straight from the MC6809 data sheet.
VOICE_SQUARE = [
    ("LDD", "direct", 5),
    ("ADDD", "direct", 6),
    ("STD", "direct", 5),
    ("ROLA", "inherent", 2),
    ("LDA", "immediate", 2),
    ("SBCA", "immediate", 2),
    ("ANDA", "direct", 4),
    ("ADDA", "direct", 4),
    ("STA", "direct", 4),
]

VOICE3_NOISE = [
    ("LSR", "direct", 6),
    ("ROR", "direct", 6),
    ("LDA", "immediate", 2),
    ("SBCA", "immediate", 2),
    ("ANDA", "immediate", 2),
    ("EORA", "direct", 4),
    ("STA", "direct", 4),
    ("LDA", "direct", 4),
    ("LSRA", "inherent", 2),
    ("LDA", "immediate", 2),
    ("SBCA", "immediate", 2),
    ("ANDA", "direct", 4),
    ("STA", "direct", 4),
]

MIX_AND_OUTPUT = [
    ("STA", "extended", 5),
]

TICK_COUNTDOWN = [
    ("DEC", "direct", 6),
    ("BNE", "relative", 3),
]

# The same loop assembled for a 6309 in native mode, for EXP-015, the
# faster-clock listening test. The instructions are identical; the counts
# are the HD6309 native-mode column of its data sheet, where a direct-page
# byte access is 3, a 16-bit one 4 (ADDD 5), a read-modify-write 5, an
# inherent shift 1, and an extended store 4. The one instruction that differs
# is the tick countdown, which the 6309 build keeps in W: DECW is 2 and the
# reload after each tick's work is off the per-sample path.
VOICE_SQUARE_6309 = [
    ("LDD", "direct", 4),
    ("ADDD", "direct", 5),
    ("STD", "direct", 4),
    ("ROLA", "inherent", 1),
    ("LDA", "immediate", 2),
    ("SBCA", "immediate", 2),
    ("ANDA", "direct", 3),
    ("ADDA", "direct", 3),
    ("STA", "direct", 3),
]

VOICE3_NOISE_6309 = [
    ("LSR", "direct", 5),
    ("ROR", "direct", 5),
    ("LDA", "immediate", 2),
    ("SBCA", "immediate", 2),
    ("ANDA", "immediate", 2),
    ("EORA", "direct", 3),
    ("STA", "direct", 3),
    ("LDA", "direct", 3),
    ("LSRA", "inherent", 1),
    ("LDA", "immediate", 2),
    ("SBCA", "immediate", 2),
    ("ANDA", "direct", 3),
    ("STA", "direct", 3),
]

MIX_AND_OUTPUT_6309 = [
    ("STA", "extended", 4),
]

TICK_COUNTDOWN_6309 = [
    ("DECW", "inherent", 2),
    ("BNE", "relative", 3),
]

CPUS = {
    "6809": (VOICE3_NOISE, VOICE_SQUARE, MIX_AND_OUTPUT, TICK_COUNTDOWN),
    "6309": (
        VOICE3_NOISE_6309,
        VOICE_SQUARE_6309,
        MIX_AND_OUTPUT_6309,
        TICK_COUNTDOWN_6309,
    ),
}


def total(block: list[tuple[str, str, int]]) -> int:
    return sum(cycles for _, _, cycles in block)


def show(title: str, block: list[tuple[str, str, int]]) -> int:
    print(f"  {title}")
    for mnemonic, mode, cycles in block:
        print(f"    {mnemonic:<6}{mode:<16}{cycles:>4}")
    subtotal = total(block)
    print(f"    {'':<22}{subtotal:>4}  subtotal")
    return subtotal


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clock", type=int, default=None,
                        help="processor clock in Hz; defaults to the CoCo 1's, "
                        "or the CoCo 3's fast clock for --cpu 6309")
    parser.add_argument(
        "--cpu",
        choices=tuple(CPUS),
        default="6809",
        help="6309 uses native-mode timings, as EXP-015's native build does",
    )
    parser.add_argument(
        "--overhead-cycles",
        type=float,
        default=1.6,
        help="per-sample share of tick and row processing, amortised, on a "
        "6809; the 6309 figure is scaled by the loop's own speedup",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    noise_block, voice_block, mix_block, tick_block = CPUS[arguments.cpu]
    clock = arguments.clock
    if clock is None:
        clock = COCO3_FAST_CLOCK if arguments.cpu == "6309" else COCO1_CLOCK

    print(f"Sample loop (every path, every sample), {arguments.cpu}"
          + (" native mode" if arguments.cpu == "6309" else ""))
    noise3 = show("voice 3 (noise, branch-free)", noise_block)
    print()
    one_voice = show("voice 2, 1, or 0 (square)", voice_block)
    print()
    mix = show("mix and output", mix_block)
    print()
    tick = show("tick countdown", tick_block)
    print()

    # Voice 0 skips its store; its sum goes straight to the DAC.
    store = voice_block[-1][2]
    loop = noise3 + one_voice * 3 - store + mix + tick
    print(f"sample loop: {loop} cycles, with no branch and no variation")
    print("(voice 0 skips its store; its sum goes straight to the DAC)")
    print(f"pitch during playback: {clock / loop:.0f} Hz")
    print()
    overhead = arguments.overhead_cycles
    if arguments.cpu == "6309":
        # The tick and row routines are the same 6809 code, so they speed up
        # by about what the loop did. Scaling the amortised share by the loop
        # ratio is an estimate of an estimate; it moves the rate by well
        # under a tenth of a percent.
        loop_6809 = (total(VOICE3_NOISE) + total(VOICE_SQUARE) * 3
                     - VOICE_SQUARE[-1][2] + total(MIX_AND_OUTPUT)
                     + total(TICK_COUNTDOWN))
        overhead = overhead * loop / loop_6809
    print(f"plus amortised tick/row work: {overhead:.2f} cycles")
    effective = loop + overhead
    print(f"effective average: {effective:.2f} cycles per sample")
    rate = clock / effective
    print(f"sample rate: {rate:.0f} Hz at {clock} Hz")
    print()
    print(f"export with: uv run python tools/export_tune.py --sample-rate {rate:.0f}")


if __name__ == "__main__":
    main()
