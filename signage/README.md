# Table signage

The exhibit table has two machines on it and a Raspberry Pi 5 driving a
larger screen behind them. The CoCo 1 sits on a small television and the
CoCo 3 on a Commodore 1703 monitor; both are doing the demonstrating. The
big screen loops a slideshow about what they are doing, so that somebody
walking past stops, reads one question, and asks it out loud.

This directory is that slideshow and the SD-card image that boots straight
into it.

## What is in here

| Path | What it is |
| --- | --- |
| `slides/index.html`, `slides/signage.css` | The slides, one `<section>` each, in the deck's palette and typeface. |
| `slides/data.js` | Every name, number and completion the slides quote. Generated; do not edit. |
| `tools/export_slide_data.py` | Runs the reference model and reads the recorded experiments to write `data.js`. |
| `tools/render_slides.py` | Photographs each slide with headless Chrome at 1920 by 1080. |
| `image/` | The image builder: a Dockerfile for the tooling, the build script, the chroot customisation, and the files laid over the Pi's root filesystem. |
| `signage.conf` | Base image, user, Wi-Fi, seconds per slide. |
| `build/` | Downloads, rendered slides and the finished image. Not in git. |

## How it works

The Pi does not run a browser. Chrome on the Mac renders the HTML slides to
PNGs at build time, the PNGs go into the image, and on the Pi a two-line
service starts `fbi` on the console at boot to loop them. There is no
desktop to start and nothing to crash; the Pi is showing the first slide a
few seconds after power. The service restarts itself if it ever dies, and
the log lives in memory so an SD card that has its power pulled all weekend
has nothing to lose.

The image starts from the stock Raspberry Pi OS Lite (64-bit) release named
in `signage.conf`, checked against its published checksum. The builder
grows it, mounts it inside a privileged Linux container, lays the service
files on top, runs `apt` in a chroot to install the viewer, creates the
user, enables the service, retires the login prompt from the display,
copies the slides in, and quiets the kernel console. The Mac is arm64 and so
is the Pi, so the chroot runs natively with no emulation.

## Building

Needs `uv`, Google Chrome, and Docker Desktop.

```sh
cd signage
make image
```

That runs three steps, each also available on its own:

1. `make data` trains the reference model and writes `slides/data.js`. It
   reruns whenever the model, its corpora or the deck's traces change.
2. `make slides` renders `build/slides/01.png` through `build/slides/NN.png`.
3. `make image` downloads the base image the first time (about 500 MB,
   cached in `build/base/`), builds `build/coco-signage.img`, and writes
   its checksum beside it. A rebuild after the first takes a few minutes.

`make verify` mounts the finished image read-only and lists the things the
boot depends on: the slides, the service link, the masked login prompt, the
user, and the boot files. It is the most this Mac can check without a Pi.

`make preview` serves the repository and opens the loop in a browser,
cycling at the configured pace. Arrow keys step through slides. Open
`index.html?slide=7` to hold one slide, which is what the renderer does.

## Writing the card

Writing to a disk is not a make target, on purpose. Use Raspberry Pi
Imager: choose **Use custom**, pick `build/coco-signage.img`, pick the
card, and say **no** to applying OS customisation, because the image
already carries its own. Or, from a terminal, find the card first and
check the identifier twice:

```bash
diskutil list
```

```bash
diskutil unmountDisk /dev/diskN && sudo dd if=build/coco-signage.img of=/dev/rdiskN bs=4m status=progress && diskutil eject /dev/diskN
```

Put the card in the Pi, connect the screen, and power it. The first boot
grows the root partition to fill the card and reboots once by itself, so
allow a minute before deciding something is wrong.

## Updating the slides

Change `slides/index.html`, run `make image`, write the card again. That is
the whole procedure, and it is the one to trust.

If the Pi is on the network there is a shortcut that skips the card. SSH
is enabled and the user and password are in `signage.conf`; Ethernet needs
nothing else, and Wi-Fi joins if `WIFI_SSID` and `WIFI_PSK` were set when
the image was built.

```bash
make slides && scp build/slides/*.png coco@coco-signage.local:/tmp/ && ssh coco@coco-signage.local 'sudo rm /opt/coco-signage/slides/*.png; sudo mv /tmp/*.png /opt/coco-signage/slides/; sudo systemctl restart coco-signage'
```

## Writing slides

The rules the deck lives by apply here, and two of them matter more on a
screen nobody is standing beside to explain:

- **Nothing on a slide that the machine did not do.** Every generated name,
  every completion, every measured number comes from `data.js`, and
  `data.js` comes from a run of the bit-exact reference model or from an
  experiment's recorded evidence. Hand-typed words are the words around
  them. To add a number, add it to the export tool with a comment naming
  the experiment it came from.
- **No runtime claim that was not measured on the physical machine.** The
  6309 rows are on a slide because Stacey measured them on the CoCo 3 on
  5 September 2026. The live training run's duration is not, because the
  CoCo 1 number has not been taken yet.
- The model invents *plausible* names. Never print that it produces real
  ones; that claim is the thing the whole table exists to take apart.

Copy in `presentation/exhibit-copy.md` is the approved wording for
anything public, and the first two slides quote the table card from it.
Most titles are questions, because a question is something a visitor can
ask; one idea per slide, and the caption is the only place for a sentence.

Everything in Hot CoCo folds to uppercase, because the MC6847 had no
lowercase and the font is faithful about it. Captions use a real sans and
keep their case. Colours come from `presentation/coco-palette.css`; never
write a hex value in a slide.

## Not yet verified on a Pi

This image has been built and inspected on the Mac but has not yet been
booted on the Pi 5. The first boot is the test, and these are the things to
look at if it does not simply show slides:

| What you see | What to try |
| --- | --- |
| Black screen, and a keyboard's caps-lock light responds | The viewer is running but not finding the display. Set `FBI_DEVICE=/dev/fb0` in `signage.conf` and rebuild; or, over SSH, edit `/etc/coco-signage.conf` and `sudo systemctl restart coco-signage`. |
| A login prompt | The service did not start. `journalctl -u coco-signage` over SSH says why. |
| A wizard asking for a username | The user was not created; `signage.conf` had an empty `SIGNAGE_USER`. |
| Wrong size or no signal on the television | Force a mode: add `video=HDMI-A-1:1920x1080@60` to the one line in `cmdline.txt` on the card's boot partition. Use the HDMI port nearest the USB-C power socket. |
| Blinking cursor over the slide | Harmless. `vt.global_cursor_default=0` is on the kernel line; if the TV still shows one, `setterm` in the launcher is the next place to look. |

Once it has booted once, it is worth making the card read-only so a pulled
plug can never corrupt it. On the Pi, `sudo raspi-config nonint do_overlayfs 0`
then reboot. Undo with `do_overlayfs 1` before any update over SSH.

## Where the code lives

The closing slide says "ask me for the code" because this repository has
no public remote yet. When it does, put the address on that slide.
