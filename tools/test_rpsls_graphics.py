"""Exercise the real 6809 graphics routines in XRoar and inspect RAM at traps.

The driver supplies deterministic keys, but rendering, learning, scoring and
frame delays execute on the emulated CoCo with the real BASIC ROMs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/reference"))
from rpsls import FrequencyTable, RuleLearner, XorShift16, outcome
from rpsls_graphics import KEY_MOVES, compile_sprites, render, save_preview
from test_xroar import (
    BASIC_11_CRC32,
    EXTENDED_BASIC_10_CRC32,
    symbol_address,
    verify_rom,
)

OUT = ROOT / "build/exp019"
# Long enough to exercise count rescaling and the old UI's 8-bit score limit.
KEYS = bytes([49] * 600) + bytes(
    ([49] * 40 + [50, 51, 52, 53] * 10 + [53] * 40 + [49, 50, 51, 52, 53] * 8) * 10
)


def driver() -> str:
    return """        org $2000
        include "text_screen.asm"
        include "rpsls_game.asm"
        include "rpsls_graphics.asm"
test_start
        lds #$7f00
        clra
        tfr a,dp
        lbsr gfx_init
test_initial
        nop
        ; All 25 pairings, each from a fresh UI and score.
        clr test_player
        clr test_cpu
test_pair_loop
        lbsr gfx_init
        lda test_player
        sta player_move
        lda test_cpu
        sta agent_move
        lbsr gfx_player_reveal
        lbsr gfx_finish_round
        ldb test_player
        lda #5
        mul
        addb test_cpu
        ldx #test_pair_results
        lda agent_result
        sta b,x
        inc test_cpu
        lda test_cpu
        cmpa #5
        blo test_pair_loop
        clr test_cpu
        inc test_player
        lda test_player
        cmpa #5
        blo test_pair_loop
test_pairs_done
        nop
        lbsr gfx_init
        ; Stage check: only the player's scissors are visible.
        lda #4
        sta player_move
        lda #2
        sta agent_move
        lbsr gfx_player_reveal
test_player_visible
        nop
        ldd $0112
        std test_ticks
        lbsr gfx_pause
        ldd $0112
        subd test_ticks
        std test_delay
        lbsr gfx_finish_round
test_both_visible
        nop
        lbsr gfx_init
        ldu #test_keys
        stu test_cursor
        ldu #test_trace
        stu test_trace_cursor
test_session_loop
        lbsr agent_choose
        sta agent_move
        ldu test_trace_cursor
        sta ,u+
        stu test_trace_cursor
        ldu test_cursor
        lda ,u+
        stu test_cursor
        lbsr gfx_decode_key
        sta player_move
        lbsr gfx_player_reveal
        lbsr gfx_finish_round
        ldu test_cursor
        cmpu #test_keys_end
        blo test_session_loop
test_session_done
        nop
        ; Invalid ASCII must neither settle a round nor touch its frame.
        ldu #test_invalid
        stu test_cursor
        clr test_invalid_count
test_invalid_loop
        ldu test_cursor
        lda ,u+
        stu test_cursor
        lbsr gfx_decode_key
        bcc test_invalid_next
        inc test_invalid_count
test_invalid_next
        ldu test_cursor
        cmpu #test_invalid_end
        blo test_invalid_loop
test_invalid_done
        nop
        ; Saturation at 999 on both counters, then a clean restart.
        ldd #998
        std gfx_wins
        std gfx_cpu_wins
        ldb #3
test_cap_loop
        pshs b
        clr agent_result
        lbsr gfx_count_result
        inc agent_result
        lbsr gfx_count_result
        inc agent_result
        lbsr gfx_count_result
        puls b
        decb
        bne test_cap_loop
        lbsr gfx_draw_scores
test_capped
        nop
        lbsr gfx_init
test_reset
        nop
test_halt
        bra test_halt

test_player rmb 1
test_cpu rmb 1
test_pair_results rmb 25
test_ticks rmb 2
test_delay rmb 2
test_cursor rmb 2
test_trace_cursor rmb 2
test_invalid_count rmb 1
test_invalid fcb 0,32,48,54,65,81,255
test_invalid_end
test_keys includebin "keys.bin"
test_keys_end
test_trace rmb test_keys_end-test_keys
        end test_start
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xroar", default=shutil.which("xroar") or "xroar")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    basic, extended = ROOT / "build/roms/bas11.rom", ROOT / "build/roms/extbas10.rom"
    verify_rom(basic, BASIC_11_CRC32, "Color BASIC 1.1")
    verify_rom(extended, EXTENDED_BASIC_10_CRC32, "Extended BASIC 1.0")
    (OUT / "keys.bin").write_bytes(KEYS)
    (OUT / "test.asm").write_text(driver())
    symbols = OUT / "test.sym"
    subprocess.run(
        [
            "lwasm",
            "--6809",
            "-I",
            "src/6809",
            "--format=decb",
            f"--symbol-dump={symbols}",
            f"--output={OUT / 'test.bin'}",
            str(OUT / "test.asm"),
        ],
        cwd=ROOT,
        check=True,
    )
    checkpoints = [
        "initial",
        "pairs_done",
        "player_visible",
        "both_visible",
        "session_done",
        "invalid_done",
        "capped",
        "reset",
    ]
    command = [
        args.xroar,
        "-ui",
        "null",
        "-machine",
        "cocous",
        "-ram",
        "32",
        "-ram-init",
        "set",
        "-bas",
        str(basic),
        "-extbas",
        str(extended),
        "-no-ratelimit",
        "-quiet",
        "-timeout",
        "300",
    ]
    for checkpoint in checkpoints:
        path = OUT / f"{checkpoint}.ram"
        path.unlink(missing_ok=True)
        # Trap BEFORE its actions: otherwise XRoar binds them to startup.
        command += [
            "-trap",
            f"pc=0x{symbol_address(symbols, 'test_' + checkpoint):04x}",
            "-trap-snap",
            str(path),
        ]
    command += [
        "-trap",
        f"pc=0x{symbol_address(symbols, 'test_halt'):04x}",
        "-trap-timeout",
        "0.01",
        "-run",
        str(OUT / "test.bin"),
    ]
    result = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, timeout=60, check=False
    )
    (OUT / "test-xroar.log").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(result.stderr)
    ram = {name: (OUT / f"{name}.ram").read_bytes() for name in checkpoints}
    for name, data in ram.items():
        assert len(data) == 32768, (name, len(data))
        magic = symbol_address(symbols, "log_magic")
        assert data[magic : magic + 8] == b"RPSLSLOG", (
            "snapshot did not capture the program"
        )

    def read(name: str, label: str, size: int = 1) -> int:
        address = symbol_address(symbols, label)
        return int.from_bytes(ram[name][address : address + size], "big")

    sprites = compile_sprites(ROOT / "assets/rpsls/hand-concept.png")

    def check_frame(name: str, expected: bytes) -> None:
        actual = ram[name][0x400:0x1C00]
        save_preview(actual, OUT / f"{name}-emulator.png")
        assert actual == expected, (
            f"{name}: {sum(a != b for a, b in zip(actual, expected))} framebuffer bytes differ"
        )

    check_frame("initial", render(sprites))
    pairs_at = symbol_address(symbols, "test_pair_results")
    assert ram["pairs_done"][pairs_at : pairs_at + 25] == bytes(
        outcome(c, p) for p in range(5) for c in range(5)
    )
    check_frame("player_visible", render(sprites, 4, None, message="HERE WE GO"))
    check_frame("both_visible", render(sprites, 4, 2, (1, 0), "YOU WIN"))
    delay = read("both_visible", "test_delay", 2)
    assert 18 <= delay <= 19, delay
    agent = RuleLearner(FrequencyTable(1, use_outcome=True), XorShift16(0x1A2B))
    trace, scores = [], [0, 0]
    for key in KEYS:
        computer = agent.choose()
        player = KEY_MOVES[key - 49]
        trace.append(computer)
        result = outcome(player, computer)
        if result != 1:
            category = 0 if result == 2 else 1
            scores[category] = min(999, scores[category] + 1)
        agent.observe(computer, player)
    at = symbol_address(symbols, "test_trace")
    assert ram["session_done"][at : at + len(KEYS)] == bytes(trace), "opponent diverged"
    assert tuple(
        read("session_done", label, 2) for label in ("gfx_wins", "gfx_cpu_wins")
    ) == tuple(scores)
    rules_at = symbol_address(symbols, "rules")
    assert ram["session_done"][rules_at : rules_at + 25] == bytes(
        value for row in agent.rules for value in row
    )
    verdict = ("COCO WINS", "DRAW", "YOU WIN")[result]
    check_frame(
        "session_done", render(sprites, player, computer, tuple(scores), verdict)
    )
    assert read("invalid_done", "test_invalid_count") == 7
    assert ram["invalid_done"][0x400:0x1C00] == ram["session_done"][0x400:0x1C00]
    assert tuple(
        read("invalid_done", label, 2) for label in ("gfx_wins", "gfx_cpu_wins")
    ) == tuple(scores)
    check_frame("capped", render(sprites, player, computer, (999, 999), verdict))
    check_frame("reset", render(sprites))
    assert ram["reset"][rules_at : rules_at + 100] == bytes(100)
    report = {
        "pairings_checked": 25,
        "session_rounds": len(KEYS),
        "opponent_parity": True,
        "framebuffers_checked": 6,
        "reveal_delay_frames": delay,
        "invalid_keys_checked": 7,
        "scores": scores,
        "saturation": 999,
        "ram_kib": 32,
        "ram_initialisation": "set",
        "hardware_tested": False,
        "sprite_bytes": sum(map(len, sprites)),
        "sprite_sha256": hashlib.sha256(b"".join(sprites)).hexdigest(),
    }
    (OUT / "evidence.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
