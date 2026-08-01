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

# (mnemonic, addressing mode, cycles) straight from the MC6809 data sheet.
VOICE_SQUARE = [
    ("LDD", "direct", 5),
    ("ADDD", "direct", 6),
    ("STD", "direct", 5),
    ("ROLA", "inherent", 2),
    ("ROL", "direct", 6),
]

VOICE3_SQUARE = [
    ("LDD", "direct", 5),
    ("ADDD", "direct", 6),
    ("STD", "direct", 5),
    ("TST", "direct", 6),
    ("BNE", "relative", 3),
    ("ROLA", "inherent", 2),
    ("ROL", "direct", 6),
    ("BRA", "relative", 3),
]

VOICE3_NOISE = [
    ("LDD", "direct", 5),
    ("ADDD", "direct", 6),
    ("STD", "direct", 5),
    ("TST", "direct", 6),
    ("BNE", "relative", 3),
    ("BCC", "relative", 3),
    ("LDA", "direct", 4),
    ("LSRA", "inherent", 2),
    ("ROL", "direct", 6),
]

MIX_AND_OUTPUT = [
    ("LDB", "direct", 4),
    ("ANDB", "immediate", 2),
    ("LDA", "B,X indexed", 5),
    ("STA", "extended", 5),
]

TICK_COUNTDOWN = [
    ("DEC", "direct", 6),
    ("BNE", "relative", 3),
]


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
    parser.add_argument("--clock", type=int, default=COCO1_CLOCK)
    parser.add_argument(
        "--noise-share",
        type=float,
        default=0.25,
        help="fraction of samples where voice 3 is a noise instrument",
    )
    parser.add_argument(
        "--overhead-cycles",
        type=float,
        default=6.5,
        help="per-sample share of tick and row processing, amortised",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    print("Sample loop, voice 3 on the square path")
    square3 = show("voice 3 (square)", VOICE3_SQUARE)
    print()
    noise3 = show("voice 3 (noise, no wrap)", VOICE3_NOISE)
    print()
    one_voice = show("voice 2, 1, or 0", VOICE_SQUARE)
    print()
    mix = show("mix and output", MIX_AND_OUTPUT)
    print()
    tick = show("tick countdown", TICK_COUNTDOWN)
    print()

    body = one_voice * 3 + mix + tick
    square_total = square3 + body
    noise_total = noise3 + body
    blended = (
        square_total * (1 - arguments.noise_share) + noise_total * arguments.noise_share
    )
    effective = blended + arguments.overhead_cycles

    print(f"per sample, voice 3 square: {square_total} cycles")
    print(f"per sample, voice 3 noise:  {noise_total} cycles")
    print(f"blended at {arguments.noise_share:.0%} noise: {blended:.1f} cycles")
    print(f"plus amortised tick/row work: {arguments.overhead_cycles:.1f} cycles")
    print(f"effective: {effective:.1f} cycles per sample")
    print()
    rate = arguments.clock / effective
    print(f"clock: {arguments.clock} Hz")
    print(f"sample rate: {rate:.0f} Hz")
    print()
    print(f"export with: uv run python tools/export_tune.py --sample-rate {rate:.0f}")


if __name__ == "__main__":
    main()
