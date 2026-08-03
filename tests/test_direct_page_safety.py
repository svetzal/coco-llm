"""No file outside the player may reach player state through the direct page.

music_player.asm declares `setdp $20`, and lwasm applies that to the whole
assembly, not to one file. So a bare reference to a player variable written
anywhere else assembles to a direct-page instruction: correct inside the
player, where DP really is $20, and silently wrong everywhere else, where it
lands in whatever page DP happens to hold.

That is not hypothetical. `std row_hook` in ui_perform assembled to `DD 24`
and wrote the playback cursor's address into $0024, in BASIC's page. The
hook variable itself kept whatever the RAM held and the player jumped there
once per row. It cost a working demo and looked like a timing fault.

This asserts on the assembled bytes rather than the source, because the
source is exactly where the mistake is invisible.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
TOP = ROOT / "src" / "6809" / "coco_melody_demo.asm"
PLAYER = "music_player.asm"

# Everything music_player.asm keeps in the direct page.
PLAYER_STATE = {
    "phases",
    "incrs",
    "scaled",
    "decays",
    "dac_acc",
    "lfsr",
    "tick_samples",
    "row_ticks",
    "rows_left",
    "repeats_left",
    "row_ptr",
    "finished",
    "voice_no",
    "cells_left",
    "row_hook",
    "ticks_cfg",
    "incr_tmp",
    "scratch",
    "saved_dp",
}

# 531A B72026        (  melody_ui.asm):00405        sta     >ticks_cfg
LISTING = re.compile(r"^([0-9A-F]{4}) ([0-9A-F]*)\s+\(\s*(\S+?)\s*\):\d+\s+(.*)$")


def listing() -> list[tuple[str, str, str]]:
    """(object bytes, source file, source text) for every assembled line."""
    with_list = subprocess.run(
        ["lwasm", "--6809", "--format=decb", "--list=-", "--output=/dev/null", str(TOP)],
        capture_output=True,
        text=True,
        check=True,
    )
    rows = []
    for line in with_list.stdout.splitlines():
        match = LISTING.match(line)
        if match and match.group(2):
            rows.append((match.group(2), match.group(3), match.group(4)))
    return rows


def test_listing_is_readable() -> None:
    """A parse that silently matched nothing would pass every check below."""
    rows = listing()
    assert len(rows) > 500
    assert any(source == PLAYER for _, source, _ in rows)
    assert any(source != PLAYER for _, source, _ in rows)


def test_saved_dp_is_never_reached_through_the_direct_page() -> None:
    """The one player variable touched while DP is not the player's.

    music_start saves the caller's DP before switching to $20 and restores it
    after switching back, so the file-level exemption below does not cover it.
    Written direct, the save landed in the caller's page and the restore read
    RAM nobody had written, handing the UI a garbage DP to poll the keyboard
    through.
    """
    offenders = [
        f"{source}:{text.strip()} -> {code}"
        for code, source, text in listing()
        if re.match(r"^\s*\S+\s+<?saved_dp\b", text.split(";")[0])
    ]
    assert not offenders, f"saved_dp must be reached as >saved_dp: {offenders}"


@pytest.mark.parametrize("name", sorted(PLAYER_STATE))
def test_player_state_is_reached_with_an_explicit_page(name: str) -> None:
    """Outside the player, say which page you mean.

    `<name` is legitimate where DP is known to be the player's - the row hook
    runs that way. `>name` is the safe form everywhere else. What must not
    appear is the bare reference, whose meaning depends on a setdp in a file
    the reader is not looking at.
    """
    bare = re.compile(rf"^\s*\S+\s+{re.escape(name)}\b")
    offenders = [
        f"{source}: {text.strip()} -> {code}"
        for code, source, text in listing()
        if source != PLAYER and bare.match(text.split(";")[0])
    ]
    assert not offenders, (
        f"bare reference to the player's {name} outside music_player.asm, "
        f"which setdp $20 makes direct-page: {offenders}"
    )
