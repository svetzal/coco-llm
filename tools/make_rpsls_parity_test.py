#!/usr/bin/env python3
"""Prove the CoCo draws the board the reference designed.

The layout was settled on the Mac, so `src/reference/rpsls_screen.py` is the
design and this asserts the 6809 agrees with it - all 512 cells, not a
sample. The first port was written without this and drew five separate
things wrong; each one would have been a one-line diff against a screen
that already existed.

State is poked in rather than played, so the test measures drawing and only
drawing. Whether the agent picks the same move as the reference is a
different question with a different answer, and mixing them would leave a
failure that could be either.

Two cases are drawn, because they exercise disjoint code:

  played  a full history, a two-digit score, a rule that fits on one row.
  wrapped the LIZARD/SCISSORS pairing, whose rule is 38 columns and has to
          hang its last word on the row below.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from rpsls import MOVES, outcome
from rpsls_screen import cells, render, result_lines

BINARY = ROOT / "build" / "coco-rpsls.bin"
SYMBOLS = ROOT / "build" / "coco-rpsls.sym"
RUNNER_ORG = 0x0C00
SCREEN = 0x0400
COLUMNS, ROWS = 32, 16
LEVEL = "THE MARK OF GIDEON"

# (player throws, agent throws, wins, rules cells proved, memory)
CASES = {
    "played": ([0, 0, 2, 0, 0, 1, 0], [2, 2, 1, 2, 2, 1, 2], 2, 3, 7),
    "wrapped": ([3], [4], 0, 1, 1),
}


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


def expected(case: str) -> list[int]:
    you, cpu, wins, rules_known, memory = CASES[case]
    reason, verdict, continuation = result_lines(
        you[-1], cpu[-1], outcome(you[-1], cpu[-1])
    )
    return cells(
        render(
            level=LEVEL,
            expects=MOVES[you[-1]],
            player_moves=you,
            agent_moves=cpu,
            reason=reason,
            verdict=verdict,
            continuation=continuation,
            player_wins=wins,
            rounds=len(you),
            rules_known=rules_known,
            memory=memory,
        )
    )


def poke(address: dict, case: str) -> list[str]:
    """Set the game state the reference was rendered from."""
    you, cpu, wins, rules_known, memory = CASES[case]
    lines = []

    def store(name: str, value: int, offset: int = 0) -> None:
        lines.append(f"        lda     #{value}")
        lines.append(f"        sta     ${address[name] + offset:04X}")

    # History rows hold the newest throw at the end.
    for index in range(len(you)):
        slot = 7 - len(you) + index
        store("history_you", you[index], slot)
        store("history_cpu", cpu[index], slot)
    store("history_len", len(you))
    store("rounds", len(you))
    store("wins", wins)
    store("memory", memory)
    # Any non-zero cell counts as proved, so the exact cells do not matter -
    # only how many, which is what the screen reports.
    for index in range(rules_known):
        store("rules", 3, index)
    store("expected", you[-1])
    store("expects_known", 1)
    # name_the_round sets the three result pointers from the last throw.
    store("player_move", you[-1])
    store("agent_move", cpu[-1])
    store("agent_result", outcome(cpu[-1], you[-1]))
    lines.append(f"        jsr     ${address['name_the_round']:04X}")
    lines.append(f"        jsr     ${address['draw_board']:04X}")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--case", default="played", choices=sorted(CASES))
    arguments = parser.parse_args()

    symbols = SYMBOLS.read_text()
    address = {
        name: symbol(symbols, name)
        for name in (
            "history_you",
            "history_cpu",
            "history_len",
            "rounds",
            "wins",
            "memory",
            "rules",
            "expected",
            "expects_known",
            "player_move",
            "agent_move",
            "agent_result",
            "name_the_round",
            "draw_board",
        )
    }
    grid = expected(arguments.case)

    lines = [
        f"; Generated EXP-013 board parity image ({arguments.case}). Do not edit.",
        f"        org     ${RUNNER_ORG:04X}",
        f"start   lds     #${RUNNER_ORG - 1:04X}",
        *poke(address, arguments.case),
        "        swi",
        "",
    ]
    for load, data in decb_segments(BINARY.read_bytes()):
        lines.append(f"        org     ${load:04X}")
        for offset in range(0, len(data), 16):
            chunk = data[offset : offset + 16]
            lines.append("        fcb     " + ",".join(f"${b:02X}" for b in chunk))

    lines.append("")
    lines += [f";! ${SCREEN + i:04X} = #${value:02X}" for i, value in enumerate(grid)]
    lines.append("")

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text("\n".join(lines), encoding="ascii")
    print(f"{arguments.case}: {COLUMNS * ROWS} cells -> {arguments.output}")


if __name__ == "__main__":
    main()
