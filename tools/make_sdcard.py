#!/usr/bin/env python3
"""Stage everything the hardware loads, ready to copy onto an SD card.

The CoCo SDC and the FujiNet both mount RS-DOS disk images, and the SDC can
also mount a plain directory of files as a drive. So the staging folder holds
each disk twice: as a `.DSK` image, and as a directory of the same `.BIN`
files under the same 8.3 names. Copy the whole folder to the card root.

The folder is built, never hand-assembled, so it cannot drift from the
binaries `make` produced. The manifest beside the disks is derived from the
binaries too: each entry's load range is read out of its DECB header, and
the Disk BASIC incantation that clears room for it is computed from that
range rather than remembered.

    make sdcard                       # build/sdcard/
    make sdcard-install DEST=/Volumes/COCO
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD = ROOT / "build"
OUT = BUILD / "sdcard"
DSK_TOOL = ROOT / "tools" / "make_rsdos_dsk.py"

# Disk BASIC reserves four graphics pages, $0600-$25FF, on every disk system.
# A program loading below that line needs them moved out of the way first.
GRAPHICS_PAGES_END = 0x2600


@dataclass(frozen=True)
class Entry:
    name: str        # 8.3 name on the disk, without the .BIN
    source: Path     # the DECB binary make built
    what: str        # the experiment, with its gloss
    machine: str     # what it needs to run
    keys: str        # what to do once it is running


@dataclass(frozen=True)
class Disk:
    name: str        # 8.3 image name, without the .DSK
    title: str
    entries: tuple[Entry, ...]
    sheet: str | None = None   # a session sheet that owns the procedure


DISKS = (
    Disk("COCOLLM", "The talk and the table", (
        Entry("LLM04", BUILD / "coco-llm.bin",
              "EXP-004, the live training run (blocks 1 and 3)",
              "CoCo 1 or CoCo 3, 32K",
              "Trains from random weights the moment it starts, one to two "
              "minutes, then parks at PRESS ANY KEY."),
        Entry("LLM05", BUILD / "coco-llm-exp5.bin",
              "EXP-005, the prompted marketing completions (block 4)",
              "CoCo 1 or CoCo 3, 32K",
              "Trains itself, parks at PRESS ANY KEY. Up/Down chooses a "
              "prompt, Enter generates."),
        Entry("LLM07", BUILD / "coco-llm-exp7.bin",
              "EXP-007, the all-RAM sentence completer (block 5)",
              "64K required: CoCo 3, or a 64K CoCo 1",
              "Right Arrow predicts and accepts, Up/Down choose, Clear "
              "resets."),
        Entry("TITLES", BUILD / "coco-titles.bin",
              "EXP-012, the fake episode titles (block 6)",
              "CoCo 1 or CoCo 3, 32K",
              "Shows sixteen titles; any key deals sixteen fresh ones."),
        Entry("RPSLS", BUILD / "coco-rpsls.bin",
              "EXP-013, the game opponent that learns (block 8)",
              "CoCo 1 or CoCo 3, 32K",
              "1-5 throw, R forgets everything. Press R before the talk."),
        Entry("MELODY", BUILD / "coco-melody-demo.bin",
              "EXP-010, the melody continuation (block 9)",
              "CoCo 1 or CoCo 3, 32K, sound out",
              "Composes for a moment, then performs. Nothing on screen "
              "during the tune."),
        Entry("MUSIC", BUILD / "coco-music.bin",
              "EXP-009, the four-voice synthesizer (table)",
              "CoCo 1 or CoCo 3, 32K, sound out",
              "Plays its tune to the end. Nothing on screen."),
        Entry("ATTN", BUILD / "coco-attention.bin",
              "EXP-011, the context-editing attention head (table)",
              "CoCo 1 or CoCo 3, 32K",
              "Up/Down chooses a question, Enter asks it, E edits the "
              "selected context record, V shows how it looked, Clear goes "
              "back. The model never changes; the screen says so."),
    )),
    Disk("BENCH309", "EXP-014, the 6309 multiplier benchmark", (
        Entry("BENCH09", BUILD / "bench6309" / "bench6809.bin",
              "plain 6809 kernel, the baseline",
              "CoCo 1 or CoCo 3", "Run 1 on the session sheet."),
        Entry("BENCH39", BUILD / "bench6309" / "bench6309.bin",
              "6809, native mode and MULD kernels, three rows",
              "CoCo 3 with a 6309 - crashes a 6809, expected",
              "Runs 2 and 3; POKE 65497,0 before EXEC for run 3."),
        Entry("BENCH39S", BUILD / "bench6309" / "bench6309safe.bin",
              "MULD without native mode, the fallback",
              "CoCo 3 with a 6309", "Only if BENCH39 hangs between rows."),
    ), sheet="experiments/EXP-014-hardware-session.md"),
    Disk("MUSIC015", "EXP-015, the faster-clock listening test", (
        Entry("MUSIC09", BUILD / "coco-music.bin",
              "the player at 0.89 MHz, 5,679 Hz",
              "CoCo 1 or CoCo 3", "Play first, and again last."),
        Entry("MUSIC2X", BUILD / "exp015" / "music-fast.bin",
              "the player at 1.79 MHz, 11,358 Hz",
              "CoCo 3", "Second."),
        Entry("MUSIC39", BUILD / "exp015" / "music-6309.bin",
              "the player in 6309 native mode, 14,405 Hz",
              "CoCo 3 with a 6309 - crashes a 6809, expected", "Third."),
    ), sheet="experiments/EXP-015-faster-clock-listening-test.md"),
    Disk("WAVE017", "EXP-017, the wavetable voices", (
        Entry("WAVE09", BUILD / "exp017" / "WAVE09.BIN",
              "triangle voices at 0.89 MHz, 5,789 Hz",
              "CoCo 1 or CoCo 3", "The one to play on the CoCo 1."),
        Entry("WAVE2X", BUILD / "exp017" / "WAVE2X.BIN",
              "triangle voices at 1.79 MHz, 11,578 Hz",
              "CoCo 3", ""),
        Entry("WAVE39", BUILD / "exp017" / "WAVE39.BIN",
              "triangle voices in 6309 native mode, 14,402 Hz",
              "CoCo 3 with a 6309 - crashes a 6809, expected", ""),
        Entry("SINE39", BUILD / "exp017" / "SINE39.BIN",
              "sine voices in 6309 native mode, 14,402 Hz",
              "CoCo 3 with a 6309 - crashes a 6809, expected", ""),
    ), sheet="experiments/EXP-017-wavetable-voices.md"),
    Disk("STEADY18", "EXP-018, the steady sample clock", (
        Entry("STEADY09", BUILD / "exp018" / "STEADY09.BIN",
              "the steady-clock player at 0.89 MHz, 4,590 Hz",
              "CoCo 1 or CoCo 3", ""),
        Entry("STEADY39", BUILD / "exp018" / "STEADY39.BIN",
              "the steady-clock player in 6309 native mode, 11,188 Hz",
              "CoCo 3 with a 6309 - crashes a 6809, expected", ""),
    ), sheet="experiments/EXP-018-steady-sample-clock.md"),
)


def decb_range(path: Path) -> tuple[int, int, int]:
    """(lowest load address, one past the highest, exec address)."""
    data = path.read_bytes()
    low, high, at, execute = 0x10000, 0, 0, None
    while at < len(data):
        kind, length, address = struct.unpack(">BHH", data[at:at + 5])
        at += 5
        if kind == 0xFF:
            execute = address
            break
        low, high = min(low, address), max(high, address + length)
        at += length
    if execute is None:
        raise SystemExit(f"{path} has no exec record; not a DECB binary")
    return low, high, execute


def incantation(disk: Disk, entry: Entry, low: int) -> list[str]:
    lines = [f'DRIVE 0,"{disk.name}"']
    if low < GRAPHICS_PAGES_END:
        lines.append("PCLEAR 1")
    lines.append(f"CLEAR 200,&H{low - 1:04X}")
    lines += [f'LOADM"{entry.name}"', "EXEC"]
    return lines


def build_disk(disk: Disk) -> None:
    folder = OUT / disk.name
    folder.mkdir(parents=True)
    arguments = []
    for entry in disk.entries:
        if not entry.source.exists():
            raise SystemExit(f"{entry.source} is missing; run make first")
        target = folder / f"{entry.name}.BIN"
        shutil.copyfile(entry.source, target)
        arguments += ["--file", f"{entry.name}.BIN={target}"]
    subprocess.run(
        ["python3", str(DSK_TOOL), "--output", str(OUT / f"{disk.name}.DSK"),
         *arguments],
        check=True,
    )


def manifest() -> str:
    lines = [
        "# SD card staging",
        "",
        "Built by `make sdcard`; do not edit, edit `tools/make_sdcard.py`.",
        "Copy this whole folder to the card root. Each disk is here twice:",
        "as a `.DSK` image, which the CoCo SDC and the FujiNet both mount,",
        "and as a directory of the same `.BIN` files, which the SDC mounts",
        "with the same `DRIVE 0` command if an image will not.",
        "",
        "Most of these load inside the graphics pages Disk BASIC reserves,",
        "so a recipe moves them out of the way when its program needs that.",
        "Load addresses are read from the binaries, not remembered.",
        "",
    ]
    for disk in DISKS:
        lines += [f"## `{disk.name}.DSK` - {disk.title}", ""]
        if disk.sheet:
            lines += [f"Procedure and what to write down: `{disk.sheet}`.", ""]
        for entry in disk.entries:
            low, high, execute = decb_range(entry.source)
            lines += [
                f"### `{entry.name}` - {entry.what}",
                "",
                f"- Needs: {entry.machine}",
                f"- Loads ${low:04X}-${high - 1:04X}, runs from ${execute:04X}",
                *([f"- {entry.keys}"] if entry.keys else []),
                "",
                "```basic",
                *incantation(disk, entry, low),
                "```",
                "",
            ]
    return "\n".join(lines)


def install(destination: Path) -> None:
    if not destination.is_dir():
        raise SystemExit(f"{destination} is not a mounted directory")
    copied = []
    for item in sorted(OUT.iterdir()):
        target = destination / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
            for file in item.iterdir():
                if not filecmp.cmp(file, target / file.name, shallow=False):
                    raise SystemExit(f"{target / file.name} did not verify")
        else:
            shutil.copyfile(item, target)
            if not filecmp.cmp(item, target, shallow=False):
                raise SystemExit(f"{target} did not verify")
        copied.append(item.name)
    print(f"installed to {destination}, verified byte-for-byte:")
    for name in copied:
        print(f"  {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--install", type=Path, metavar="DEST",
                        help="after staging, copy to this mounted card and verify")
    arguments = parser.parse_args()

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for disk in DISKS:
        build_disk(disk)
    (OUT / "MANIFEST.md").write_text(manifest(), encoding="utf-8")
    print(f"staged {len(DISKS)} disks in {OUT.relative_to(ROOT)}:")
    for disk in DISKS:
        print(f"  {disk.name}.DSK  ({len(disk.entries)} files)")

    if arguments.install:
        install(arguments.install)


if __name__ == "__main__":
    main()
