# FujiNet for the CoCo

Working notes for the FujiNet cartridge: what it is, how the SD card is used,
why `DIR` fails on an empty card, and how this project's disk images get onto
the machine through it. Sourced facts cite the guide or hardware README they
come from. Inferences are marked.

## What the cartridge is

The CoCo FujiNet is an ESP32 in a cartridge. The cartridge ROM is HDB-DOS, the
DriveWire build of Disk Extended Color BASIC, so the CoCo sees a disk
controller. The ESP32 answers the DriveWire protocol over a pigtail that plugs
into the SERIAL I/O port on the back of the CoCo. Rev0000 boards draw 5 V from
the cartridge port, so the USB socket is only for flashing and debug logging
(fujinet-hardware README).

Two DIP switches on top of the cartridge pick the ROM image and the serial rate
(fujinet-hardware README, Stephens guide):

| Machine | SW1-1 | SW1-2 | Serial rate |
| --- | --- | --- | --- |
| CoCo 1 | ON | ON | 38,400 |
| CoCo 2 | OFF | ON | 57,600 |
| CoCo 3 | ON | OFF | 115,200 |
| Dragon 32/64 | OFF | OFF | 57,600 |

Power the CoCo off before inserting or removing the cartridge or the pigtail.

The 115,200 rate on the CoCo 3 needs the double-speed poke, which HDB-DOS
applies on every disk access (Stephens guide). The CoCo 1 ROM runs at 38,400
with no speed poke. Inference: loading through FujiNet on the CoCo 1 leaves the
clock at its normal rate, so the timing contract holds. If a run on a CoCo 3
is ever timed, enter `POKE 65496,0` after loading and before starting it.

## The SD card

- Format: FAT32. A 32 GB card is fine. The guide recommends 64 GB or less and
  a reliable brand.
- The card holds disk image files, `.DSK` for floppies and `.VHD` for hard
  drives. It is not a CoCo disk itself. Nothing on the CoCo lists the card's
  files except the CONFIG program.
- The card appears as a host slot named `SD`, in capitals. It is set up
  automatically in host slot 1.
- Images on the SD card can be mounted read-write. Images from a TNFS server
  are always read-only.

To format the card on the Mac, find its device with `diskutil list`, then:

```sh
diskutil eraseDisk FAT32 FUJINET MBRFormat /dev/diskN
```

Disk Utility does the same if the scheme is set to Master Boot Record and the
format to MS-DOS (FAT). A 32 GB card usually ships as FAT32 already.

## Why `DIR` gives `?IO ERROR` on an empty card

`DIR` is a Disk BASIC command. It reads the directory track of the disk image
mounted in HDB-DOS drive 0. It does not read the SD card. On a freshly
formatted card there is no image to mount, so drive 0 is empty after CONFIG
exits, the read fails, and BASIC reports `?IO ERROR`.

Inference, not a sourced statement. The guide does not describe the empty-slot
case. Two checks confirm it:

1. In CONFIG, press the right arrow to open the Drives screen. Slot 0 should
   be empty.
2. Create an image on the card. Press `ENTER` on the `SD` host, press `N`,
   answer `1` for the count, and give it a name. Select the new image, choose
   slot 0, and press `W` to mount it read-write. Press `BREAK`. At the `OK`
   prompt `DIR` lists an empty directory and reports free granules.

If step 2 also fails, the card itself is the problem. Reformat as FAT32 with
Master Boot Record, and check it is seated. The debug log described below
shows whether the firmware mounted the card at boot.

## CONFIG, the FujiNet control panel

CONFIG runs from a disk image the firmware mounts in slot 0 at power-on, via
HDB-DOS's `AUTOEXEC.BAS`. The first screen is the WiFi list. Pick a 2.4 GHz
network with the arrows and `ENTER`, then type the password. `SHIFT` gives
capitals. `H` enters a hidden network name and `R` rescans.

The Hosts screen follows. Eight host slots hold `SD` and TNFS server names.
Keys on this screen:

| Key | Action |
| --- | --- |
| `1`–`8` or `E` | Edit that host slot |
| `ENTER` | Browse the highlighted host |
| Right arrow | Drives screen |
| `C` | Configuration screen: SSID, IP address, firmware version |
| `L` | Boot the game lobby, where implemented |
| `BREAK` | Exit, mount the chosen images, reset the CoCo |

Browsing a host: `ENTER` opens a directory or picks an image, the left arrow
goes up a level, `F` sets a filename filter, `N` creates a new 157 KB image
in the current folder, and `C` copies an image between hosts. After picking an
image, choose a drive slot 0 to 3, then `ENTER` for read-only or `W` for
read-write.

On the Drives screen, `E` ejects the highlighted slot, `CLEAR` empties all
four, and `R` or `W` changes a slot's mode.

To get back to CONFIG from BASIC, press the RESET button on the back of the
CoCo, then type `DOS`. Reset remounts the CONFIG image in slot 0.

## Loading this project's programs

`make sdcard` stages every disk image the show uses under `build/sdcard/`.
Each disk is there twice: as a `.DSK` image, and as a folder of the same
binaries for the CoCo SDC. FujiNet uses only the images. The folders do it no
harm.

Copy the staging folder to the card:

```sh
make sdcard-install DEST=/Volumes/FUJINET
```

Then on the CoCo:

1. In CONFIG, press `ENTER` on the `SD` host.
2. Select the image, for example `RPSLS.DSK`, choose slot 0, press `ENTER`.
3. Press `BREAK`. The CoCo resets to `OK`.
4. `DIR` lists the disk. `LOADM "NAME"` then `EXEC` runs a binary, or
   `RUNM "NAME"` does both in one step.

Mount a second image in slot 1 and switch to it with `DRIVE #1`. HDB-DOS needs
the `#`; plain `DRIVE 1` is the Disk BASIC form and does not apply.

`build/sdcard/MANIFEST.md` lists each binary's load range and the `CLEAR`
line it needs. Programs that load below `$2600` need that line before `LOADM`,
exactly as with the SDC.

## Firmware and debugging

- The FujiNet Flasher at
  <https://github.com/FujiNetWIFI/fujinet-flasher/releases> downloads and
  installs releases. Choose Tandy CoCo as the platform.
- The USB socket is USB mini. The Mac needs the Silicon Labs CP210x driver.
- Hold the `A` button on the cartridge, the one nearest the front when
  inserted, until the flasher starts writing.
- The flasher's Serial Debug Output button shows the firmware log while the
  CoCo runs. This is the place to look when a mount or the card fails.
- Nightly builds are at
  <https://github.com/FujiNetWIFI/fujinet-firmware/releases/tag/nightly>,
  files named `fujinet-COCO-…`.

Earlier prototype boards needed USB power before the CoCo came up and a press
of the ESP32's EN button to boot (Leaded Solder, December 2024). Rev0000
boards took the cartridge-port power fix, so that procedure should not be
needed on current hardware.

## Network software

The public server `tnfs.fujinet.online` has a `COCO` folder with `NEWS.DSK`,
`WEATHER.DSK`, `NETCAT.DSK`, `WIKI.DSK` and `LOBBY.DSK`. Add it as a host,
browse, mount, `BREAK`. These images are read-only.

## Emulation

FujiNet-PC built with `./build.sh -b -p COCO` serves the same protocol to
XRoar through the Becker port, with the `hdbdw3bc3.rom` cartridge ROM. This
would let `tools/test_xroar.py` exercise the FujiNet load path without the
hardware. Not tried yet.

## Sources

- Rich Stephens, [FujiNet for CoCo: The
  Basics](https://colorcomputerarchive.com/repo/Documents/Manuals/Hardware/FujiNet%20for%20CoCo%20-%20The%20Basics%20(Rich%20Stephens).pdf),
  revision 2026-03-02. The CONFIG key tables, HDB-DOS notes, SD card advice
  and flashing procedure come from here.
- FujiNet, [fujinet-hardware
  Coco](https://github.com/FujiNetWIFI/fujinet-hardware/tree/master/Coco).
  DIP switch table, power, LEDs, connector.
- FujiNet docs, [CoCo getting
  started](https://fujinetwifi.github.io/fujinet-docs/getting-started/coco/),
  [CoCo CONFIG](https://fujinetwifi.github.io/fujinet-docs/config/coco/), and
  [virtual disk
  drives](https://fujinetwifi.github.io/fujinet-docs/features/disk-drives/).
- Leaded Solder, [Ascending Mount
  FujiNet](https://www.leadedsolder.com/2024/12/17/coco-fujinet.html),
  December 2024. Prototype-board boot problems.
- FujiNet wiki, [Run FujiNet with XRoar for
  CoCo](https://github.com/FujiNetWIFI/fujinet-firmware/wiki/Run-FujiNet-with-Xroar-for-CoCo).
- Cloud-9, [HDB-DOS User
  Manual](http://cloud9tech.com/Cloud-9/Support/HDB-DOS%20User%20Manual.pdf).
