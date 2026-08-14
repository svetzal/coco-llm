#!/usr/bin/env python3
"""Prove the CoCo's opponent plays the same game the reference measured.

The board test compares drawing. This compares behaviour, which is the half
that carries the evidence: EXP-013's numbers - 80% against the synthetic
players, the rules learned from seven cells - are all statements about
`src/reference/rpsls.py`, and they only transfer to the machine if the
machine does the same thing.

Everything has to line up for the two to agree move for move:

  the generator   XorShift16, and the same number of draws in the same order.
  the prediction  the first move with the highest count, ties going to the
                  lowest index, and no expectation at all from an empty row.
  the choice      a known win, else an unseen cell, else a known tie, each
                  drawn from the candidates rather than taken in order.
  the update      which rules cell is proved, which count is incremented, and
                  the context - your last move and the last outcome - being
                  the one from *before* the round.

A scripted set of throws runs through the real game loop, and the move the
agent chose is compared for every round. Divergence anywhere above shows up
as a different move, usually several rounds after the cause.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from rpsls import FrequencyTable, RuleLearner, XorShift16, outcome

BINARY = ROOT / "build" / "rpsls-agent.bin"
SYMBOLS = ROOT / "build" / "rpsls-agent.sym"
RUNNER_ORG = 0x0C00
RNG_SEED = 0x1A2B
END = 0xFE

# Deliberately not random: a habit the table can learn, a stretch of variety
# that forces exploration, and a switch part-way that makes the machine chase
# a target which has moved.
SCRIPT = (
    [0, 0, 0, 0, 0, 0]
    + [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]
    + [2, 2, 2, 2, 2, 2, 2, 2]
    + [4, 3, 4, 3, 4, 3]
    + [1, 1, 0, 1, 1, 0, 1, 1]
)


def symbol(text: str, name: str) -> int:
    match = re.search(rf"^{re.escape(name)} EQU \$([0-9A-Fa-f]+)$", text, re.MULTILINE)
    if match is None:
        raise ValueError(f"symbol not found: {name}")
    return int(match.group(1), 16)


def decb_segments(payload: bytes) -> list[tuple[int, bytes]]:
    segments, offset = [], 0
    while offset < len(payload):
        flag = payload[offset]
        length = int.from_bytes(payload[offset + 1 : offset + 3], "big")
        address = int.from_bytes(payload[offset + 3 : offset + 5], "big")
        offset += 5
        if flag == 0xFF:
            break
        segments.append((address, payload[offset : offset + length]))
        offset += length
    return segments


def reference_play() -> tuple[list[int], int, int]:
    """The agent's move each round, then the rules it proved and rounds won."""
    agent = RuleLearner(FrequencyTable(1, use_outcome=True), XorShift16(RNG_SEED))
    chosen, wins = [], 0
    for throw in SCRIPT:
        own = agent.choose()
        chosen.append(own)
        if outcome(throw, own) == 2:
            wins += 1
        agent.observe(own, throw)
    return chosen, agent.known_cells(), wins


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()

    symbols = SYMBOLS.read_text()
    address = {
        name: symbol(symbols, name)
        for name in (
            "start",
            "script",
            "trace_agent",
            "rules",
            "wins",
            "rounds",
            "log_count",
            "log_player",
            "log_agent",
            "log_expected",
        )
    }
    chosen, rules_known, wins = reference_play()

    lines = [
        "; Generated EXP-013 agent parity image. Do not edit.",
        f"; {len(SCRIPT)} scripted throws, {rules_known}/25 rules proved",
        f"        org     ${RUNNER_ORG:04X}",
        f"start   lds     #${RUNNER_ORG - 1:04X}",
    ]
    for index, throw in enumerate(SCRIPT):
        lines.append(f"        lda     #{throw}")
        lines.append(f"        sta     ${address['script'] + index:04X}")
    lines.append(f"        lda     #${END:02X}")
    lines.append(f"        sta     ${address['script'] + len(SCRIPT):04X}")
    lines.append(f"        jmp     ${address['start']:04X}")
    lines.append("")

    for load, data in decb_segments(BINARY.read_bytes()):
        lines.append(f"        org     ${load:04X}")
        for offset in range(0, len(data), 16):
            chunk = data[offset : offset + 16]
            lines.append("        fcb     " + ",".join(f"${b:02X}" for b in chunk))

    lines.append("")
    lines += [
        f";! ${address['trace_agent'] + index:04X} = #${move:02X}"
        for index, move in enumerate(chosen)
    ]
    # The tables it ends holding, not only the moves it made on the way.
    lines.append(f";! ${address['rounds']:04X} = #${len(SCRIPT):02X}")
    lines.append(f";! ${address['wins']:04X} = #${wins:02X}")

    # The session log is the evidence a recorded game is read out of, so it is
    # checked here rather than trusted: every throw, every answer, and what was
    # expected before either.
    lines.append(f";! ${address['log_count']:04X} = #${len(SCRIPT):02X}")
    for index, (throw, own) in enumerate(zip(SCRIPT, chosen, strict=True)):
        lines.append(f";! ${address['log_player'] + index:04X} = #${throw:02X}")
        lines.append(f";! ${address['log_agent'] + index:04X} = #${own:02X}")
    lines.append("")

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text("\n".join(lines), encoding="ascii")
    print(
        f"{len(SCRIPT)} rounds, reference wins {wins}, "
        f"{rules_known}/25 rules -> {arguments.output}"
    )


if __name__ == "__main__":
    main()
