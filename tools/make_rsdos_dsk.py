#!/usr/bin/env python3
"""Build an RS-DOS (Disk BASIC) floppy image from DECB binaries.

Written rather than shelled out to toolshed's `decb` so the disk that goes to
the hardware is produced by the same `make` as everything else, with no tool
to install first. The format is the standard 35-track single-sided one every
CoCo SDC and FujiNet reads.

  35 tracks x 18 sectors x 256 bytes
  track 17 is the directory: sector 2 is the granule table, 3-11 the entries
  a granule is 9 sectors, and tracks 0-16 and 18-34 supply 68 of them
"""

from __future__ import annotations

import argparse
from pathlib import Path

TRACKS, SECTORS, SECTOR_SIZE = 35, 18, 256
TRACK_SIZE = SECTORS * SECTOR_SIZE
DIRECTORY_TRACK = 17
GRANULE_SECTORS = 9
GRANULES = 68
FREE = 0xFF
TYPE_MACHINE_CODE = 2
BINARY = 0x00


def granule_offset(granule: int) -> int:
    """Granules run over every track but the directory track, two per track."""
    track, half = divmod(granule, 2)
    if track >= DIRECTORY_TRACK:
        track += 1
    return track * TRACK_SIZE + half * GRANULE_SECTORS * SECTOR_SIZE


def sector_offset(track: int, sector: int) -> int:
    return track * TRACK_SIZE + (sector - 1) * SECTOR_SIZE


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--file",
        dest="files",
        action="append",
        required=True,
        metavar="NAME.EXT=PATH",
        help="a file to place on the disk, for example BENCH39.BIN=build/x.bin",
    )
    arguments = parser.parse_args()

    image = bytearray(b"\xff" * (TRACKS * TRACK_SIZE))
    table = bytearray([FREE] * GRANULES)
    entries: list[bytes] = []
    next_granule = 0

    for specification in arguments.files:
        name, _, source = specification.partition("=")
        stem, _, extension = name.partition(".")
        if len(stem) > 8 or len(extension) > 3:
            raise SystemExit(f"{name} is not an 8.3 name")
        payload = Path(source).read_bytes()

        needed = -(-len(payload) // (GRANULE_SECTORS * SECTOR_SIZE))
        if next_granule + needed > GRANULES:
            raise SystemExit("disk full")
        first = next_granule
        for index in range(needed):
            granule = first + index
            chunk = payload[
                index * GRANULE_SECTORS * SECTOR_SIZE : (index + 1)
                * GRANULE_SECTORS
                * SECTOR_SIZE
            ]
            start = granule_offset(granule)
            image[start : start + len(chunk)] = chunk
            if index + 1 < needed:
                table[granule] = granule + 1
            else:
                used = -(-len(chunk) // SECTOR_SIZE)
                table[granule] = 0xC0 + used
        next_granule += needed

        last = len(payload) % SECTOR_SIZE or SECTOR_SIZE
        entries.append(
            stem.ljust(8).encode("ascii")
            + extension.ljust(3).encode("ascii")
            + bytes([TYPE_MACHINE_CODE, BINARY, first])
            + last.to_bytes(2, "big")
            + bytes(16)
        )

    granule_table = sector_offset(DIRECTORY_TRACK, 2)
    image[granule_table : granule_table + GRANULES] = table

    directory = sector_offset(DIRECTORY_TRACK, 3)
    for index, entry in enumerate(entries):
        image[directory + index * 32 : directory + (index + 1) * 32] = entry
    # $FF in the first byte ends the directory, and the image starts that way.

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(bytes(image))
    print(
        f"{arguments.output}: {len(entries)} files, "
        f"{next_granule} of {GRANULES} granules used"
    )
    for specification in arguments.files:
        name, _, source = specification.partition("=")
        print(f"  {name:<12} {Path(source).stat().st_size:6d} bytes")


if __name__ == "__main__":
    main()
