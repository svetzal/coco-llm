#!/usr/bin/env python3
"""Play the CoCo game and keep the session.

The Mac capture tool records a stand-in: the same tables and the same
arithmetic, but a terminal. This records the thing actually played. That
matters because the whole question EXP-013 has left is how a *person* behaves
against this opponent, and a person behaves differently in front of a CoCo
screen than a scrolling prompt.

XRoar is launched with a trap on the halt loop the `Q` key parks the program
on. When it fires, XRoar writes a snapshot and quits, and the session is read
out of the RAM in that snapshot.

The log is found by searching the snapshot for a magic string the program
keeps immediately in front of it, so nothing here has to know XRoar's
snapshot format - only that RAM appears in it contiguously.

Play, then press Q. Output is the same schema the Mac tool writes, so both
kinds of session replay through the same scorer.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from rpsls import MOVES

BINARY = ROOT / "build" / "coco-rpsls.bin"
SYMBOLS = ROOT / "build" / "coco-rpsls.sym"
DEFAULT_OUTPUT = ROOT / "experiments" / "data" / "EXP-013-captures.jsonl"
DEFAULT_XROAR = Path(shutil.which("xroar") or "/opt/homebrew/opt/xroar/bin/xroar")
BASIC_ROM = ROOT / "build" / "roms" / "bas11.rom"
EXTENDED_ROM = ROOT / "build" / "roms" / "extbas10.rom"

MAGIC = b"RPSLSLOG"
LOG_MAX = 200
LOG_RESETS = 16
NO_EXPECTATION = 0xFF
SCHEMA = "exp013-capture/1"


def symbol(name: str) -> int:
    import re

    match = re.search(
        rf"^{re.escape(name)} EQU \$([0-9A-Fa-f]+)$", SYMBOLS.read_text(), re.MULTILINE
    )
    if match is None:
        raise ValueError(f"symbol not found: {name}")
    return int(match.group(1), 16)


def read_log(snapshot: Path) -> dict:
    """Pull the session out of the snapshot, by finding the magic in front of it."""
    payload = snapshot.read_bytes()
    at = payload.find(MAGIC)
    if at < 0:
        raise SystemExit(
            "no session log in the snapshot: the magic string was not found, "
            "so either the program never reached the halt loop or the "
            "snapshot does not carry RAM verbatim"
        )
    if payload.find(MAGIC, at + 1) >= 0:
        raise SystemExit("the magic string appears twice; cannot tell which is RAM")

    cursor = at + len(MAGIC)
    count = payload[cursor]
    resets_held = payload[cursor + 1]
    resets = list(payload[cursor + 2 : cursor + 2 + LOG_RESETS])[:resets_held]
    base = cursor + 2 + LOG_RESETS
    return {
        "moves": list(payload[base : base + count]),
        "opponent": list(payload[base + LOG_MAX : base + LOG_MAX + count]),
        "predicted": [
            -1 if value == NO_EXPECTATION else value
            for value in payload[base + 2 * LOG_MAX : base + 2 * LOG_MAX + count]
        ],
        "resets_after_round": resets,
        "truncated": count >= LOG_MAX,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True, help="e.g. stacey-coco-01")
    parser.add_argument("--xroar", type=Path, default=DEFAULT_XROAR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=int, default=3600)
    arguments = parser.parse_args()

    if not BINARY.exists():
        raise SystemExit(f"build it first: {BINARY} is missing (make rpsls-bin)")

    print("1-5 to throw, R to wipe its memory, Q to end the session and save.")
    print("The window closes itself when you press Q.\n")

    with tempfile.TemporaryDirectory(prefix="coco-rpsls-") as directory:
        snapshot = Path(directory) / "session.sna"
        subprocess.run(
            [
                str(arguments.xroar),
                "-machine",
                "cocous",
                "-ram",
                "32",
                "-bas",
                str(BASIC_ROM),
                "-extbas",
                str(EXTENDED_ROM),
                "-ratelimit",
                "-trap-snap",
                str(snapshot),
                "-trap",
                f"pc=0x{symbol('session_halt'):04x}",
                "-timeout",
                str(arguments.timeout),
                "-run",
                str(BINARY),
            ],
            check=True,
        )
        if not snapshot.exists():
            raise SystemExit(
                "no snapshot written: the session was not ended with Q, so "
                "nothing was saved. The game itself is unharmed; play again."
            )
        session = read_log(snapshot)

    played = len(session["moves"])
    if not played:
        print("no rounds played, nothing recorded")
        return

    record = {
        "schema": SCHEMA,
        "label": arguments.label,
        "recorded_utc": datetime.now(UTC).isoformat(),
        "mode": "coco",
        "seed": 0x1A2B,
        **{key: value for key, value in session.items() if key != "truncated"},
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record) + "\n")

    hits = sum(
        guess == move
        for guess, move in zip(session["predicted"], session["moves"], strict=True)
        if guess >= 0
    )
    guessed = sum(1 for guess in session["predicted"] if guess >= 0)
    print(f"{played} rounds recorded to {arguments.output}")
    if guessed:
        print(
            f"it named your throw {hits} of the {guessed} times it had an "
            f"expectation ({100 * hits / guessed:.0f}%, chance is 20%)"
        )
    if session["resets_after_round"]:
        print(f"memory wiped after rounds: {session['resets_after_round']}")
    if session["truncated"]:
        print(f"note: the log holds {LOG_MAX} rounds and filled up")
    print(f"first throws: {[MOVES[m] for m in session['moves'][:6]]}")


if __name__ == "__main__":
    main()
