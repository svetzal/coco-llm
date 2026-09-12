# WOODHAVEN Wi-Fi bridge

A Raspberry Pi 5 that broadcasts a Wi-Fi network called WOODHAVEN and
bridges it onto its Ethernet port. Anything that joins the Wi-Fi is on the
same network segment as anything plugged into the Ethernet, with no
routing, no NAT and no second subnet in between. It exists so the FujiNet,
which has only a 2.4 GHz radio, can reach the computers on the table's
wired network.

## What is in here

| Path | What it is |
| --- | --- |
| `make-image.sh` | Builds the card image on the Mac and writes it to a card. |
| `bridge.conf.example` | Network name, key, channel, country, login. Copy to `bridge.conf`, which git ignores because the repository is public. |
| `build/` | The finished image and its checksum. Not in git. |

## How it works

The image is the stock Raspberry Pi OS Lite (64-bit) release that the
signage image also starts from, checked against its published checksum.
Nothing inside the Linux root filesystem is touched on the Mac. Instead
the builder mounts the FAT boot partition, which macOS can do by itself,
and drops the first-boot files this release of Raspberry Pi OS reads
through cloud-init: `user-data`, `network-config`, and the `ssh` marker.
No Docker, no chroot.

On the Pi's first boot, cloud-init creates the login user and masks the
console wizard, enables SSH, sets the Wi-Fi country, and writes three
NetworkManager profiles:

- `br0`, a bridge with spanning tree off. It takes an address from DHCP if
  the Ethernet has a server and falls back to a link-local one if not, so
  `woodhaven-bridge.local` answers either way. Its IPv6 is link-local
  only, so the bridge never goes down for want of an address.
- `eth0-port`, the Ethernet port as a port of the bridge.
- `WOODHAVEN`, the Wi-Fi radio as an access point that is also a port of
  the bridge. 2.4 GHz, channel 6, WPA2-PSK with CCMP, no management-frame
  protection: the plainest combination an ESP32 joins.

Then it reboots once and comes up with the profiles in place. The whole
first boot takes about two minutes.

## Building and writing the card

Needs `openssl@3` from Homebrew for the password hash.

```bash
cp wifi-bridge/bridge.conf.example wifi-bridge/bridge.conf
```

Fill in `WIFI_PSK`, then:

```bash
wifi-bridge/make-image.sh
```

Put a card in the Mac, find it, and check the identifier twice:

```bash
diskutil list external physical
```

```bash
wifi-bridge/make-image.sh write /dev/diskN
```

The write step refuses anything that is not removable external media. It
tries without `sudo` first, since macOS hands removable devices to the
logged-in user, and asks for a password only if it must.

## Using it

Plug the Pi's Ethernet into the wired network, power it, and wait two
minutes. Join WOODHAVEN from the FujiNet or a laptop. Addresses come from
whatever hands them out on the wired side; if nothing does, give the
wired machines and the Wi-Fi clients static addresses in the same subnet.

SSH is on: `ssh coco@woodhaven-bridge.local`, password in `bridge.conf`.
Useful there:

```bash
nmcli device status
```

```bash
nmcli connection show
```

```bash
journalctl -u NetworkManager -b
```

## Not yet verified on a Pi

This image was built and inspected on the Mac on 12 September 2026 and
has not yet been booted. Things to look at if it does not simply work:

| What you see | What to try |
| --- | --- |
| A wizard asking for a username on the console | cloud-init did not run; `sudo cloud-init status --long` and `/var/log/cloud-init.log` say why. |
| No WOODHAVEN network | Over Ethernet, `nmcli device status` should show `wlan0` as `connected` to `WOODHAVEN`. If `unavailable`, `rfkill list` and `iw reg get`; the country was not set. |
| Joined, but no wired machine answers | `bridge link` should list both `eth0` and `wlan0` under `br0`. If only one, `nmcli connection up eth0-port` or `nmcli connection up WOODHAVEN` and read the error. |
| A laptop joins but the FujiNet does not | The FujiNet wants WPA2 and 2.4 GHz, both already set. Try channel 1 or 11 in `bridge.conf` and rebuild, or on the Pi `nmcli connection modify WOODHAVEN wifi.channel 1 && nmcli connection up WOODHAVEN`. |
