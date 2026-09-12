#!/bin/bash
# Build the WOODHAVEN bridge SD-card image on the Mac, and write it to a card.
#
#   ./make-image.sh            builds build/woodhaven-bridge.img
#   ./make-image.sh write /dev/diskN   writes the built image to that card
#
# The image is the stock Raspberry Pi OS Lite (64-bit) release the signage
# image also starts from, with first-boot files dropped on its FAT boot
# partition. Nothing is changed inside the Linux root filesystem here; the
# Pi does that itself on first boot through cloud-init, which this release
# of Raspberry Pi OS reads from /boot/firmware. That is why no Docker or
# chroot is needed: macOS can mount the FAT partition on its own.
#
# On first boot the Pi creates the user, enables SSH, sets the Wi-Fi
# country, writes three NetworkManager profiles (a bridge br0, eth0 as a
# port of it, wlan0 as an access point that is also a port of it), and
# reboots once. From then on anything that joins the Wi-Fi is on the same
# Ethernet segment as whatever is plugged into the Pi.

set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
BUILD="$HERE/build"
IMG="$BUILD/woodhaven-bridge.img"
BASE_DIR="$HERE/../signage/build/base"

# shellcheck source=../signage/signage.conf
. "$HERE/../signage/signage.conf"   # BASE_IMAGE_URL, BASE_IMAGE_SHA256
[ -f "$HERE/bridge.conf" ] || { echo "no bridge.conf; copy bridge.conf.example and fill in WIFI_PSK" >&2; exit 1; }
# shellcheck source=bridge.conf
. "$HERE/bridge.conf"
[ -n "$WIFI_PSK" ] || { echo "WIFI_PSK is empty in bridge.conf" >&2; exit 1; }

log() { printf '\n==> %s\n' "$*"; }

DEV=
cleanup() {
  set +e
  if [ -n "$DEV" ]; then
    diskutil unmountDisk "$DEV" >/dev/null 2>&1
    hdiutil detach "$DEV" >/dev/null 2>&1
  fi
}
trap cleanup EXIT

# ------------------------------------------------------------------ write --
if [ "${1:-}" = write ]; then
  CARD="${2:-}"
  [ -n "$CARD" ] || { echo "usage: $0 write /dev/diskN" >&2; exit 1; }
  [ -f "$IMG" ] || { echo "no image at $IMG; run $0 first" >&2; exit 1; }
  INFO=$(diskutil info "$CARD")
  echo "$INFO" | grep -q 'Removable Media: *Removable' || { echo "$CARD is not removable media; refusing" >&2; exit 1; }
  echo "$INFO" | grep -qE 'Device Location: *External|Protocol: *(USB|Secure Digital)' || { echo "$CARD is not an external card; refusing" >&2; exit 1; }
  RAW="/dev/r${CARD#/dev/}"
  log "Writing $IMG to $RAW"
  echo "$INFO" | grep -E 'Device / Media Name|Disk Size'
  diskutil unmountDisk "$CARD"
  if [ -w "$RAW" ]; then
    dd if="$IMG" of="$RAW" bs=4m status=progress
  else
    echo "need root to write $RAW"
    sudo dd if="$IMG" of="$RAW" bs=4m status=progress
  fi
  sync
  diskutil eject "$CARD"
  log "Done. Put the card in the Pi."
  exit 0
fi

# ------------------------------------------------------------------ fetch --
log "Base image"
mkdir -p "$BUILD" "$BASE_DIR"
BASE_XZ="$BASE_DIR/$(basename "$BASE_IMAGE_URL")"
if [ ! -f "$BASE_XZ" ]; then
  echo "downloading $BASE_IMAGE_URL"
  curl -fL --progress-bar -o "$BASE_XZ.part" "$BASE_IMAGE_URL"
  mv "$BASE_XZ.part" "$BASE_XZ"
fi
echo "$BASE_IMAGE_SHA256  $BASE_XZ" | shasum -a 256 -c -

log "Decompressing"
rm -f "$IMG"
xz -dc -T0 "$BASE_XZ" > "$IMG"

# ------------------------------------------------------------ password --
# SHA-512 crypt hash, the form userconf and cloud-init both take.
OPENSSL=openssl
[ -x /opt/homebrew/opt/openssl@3/bin/openssl ] && OPENSSL=/opt/homebrew/opt/openssl@3/bin/openssl
HASH=$("$OPENSSL" passwd -6 "$BRIDGE_PASSWORD") || { echo "openssl passwd -6 failed; brew install openssl@3" >&2; exit 1; }

# ------------------------------------------------------------------ mount --
log "Mounting the boot partition"
DEV=$(hdiutil attach -imagekey diskimage-class=CRawDiskImage -nomount "$IMG" 2>/dev/null | awk 'NR==1{print $1}')
[ -n "$DEV" ] || { echo "hdiutil attach failed" >&2; exit 1; }
diskutil mount "${DEV}s1" >/dev/null
BOOT=$(diskutil info "${DEV}s1" | sed -n 's/^ *Mount Point: *//p')
[ -d "$BOOT" ] && [ -f "$BOOT/cmdline.txt" ] || { echo "boot partition did not mount" >&2; exit 1; }
echo "$DEV mounted at $BOOT"

# ------------------------------------------------------------- first boot --
log "First-boot files"

# cloud-init reads this file on first boot only. YAML: spaces, not tabs.
cat > "$BOOT/user-data" <<EOF
#cloud-config
# WOODHAVEN Wi-Fi to Ethernet bridge. Written by wifi-bridge/make-image.sh.
hostname: $BRIDGE_HOSTNAME
manage_etc_hosts: true
timezone: $TIMEZONE
ssh_pwauth: true

# On Raspberry Pi OS this renames the stock 'pi' user, sets the password,
# and masks the console wizard that would otherwise wait for a keyboard.
users:
  - name: $BRIDGE_USER
    hashed_passwd: '$HASH'
    lock_passwd: false
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    groups: [adm, dialout, cdrom, audio, users, sudo, video, games, plugdev, input, gpio, spi, i2c, netdev, render]

write_files:
  # NetworkManager must not invent a DHCP profile for eth0 of its own;
  # eth0 belongs to the bridge.
  - path: /etc/NetworkManager/conf.d/10-no-auto-default.conf
    permissions: '0644'
    content: |
      [main]
      no-auto-default=*

  # The bridge. Its own address is optional: it takes one from DHCP if the
  # Ethernet has a server and falls back to a link-local one if not, so
  # $BRIDGE_HOSTNAME.local answers either way. The bridge stays up whether
  # or not it has an IPv4 address, which is what keeps the ports bridged.
  - path: /etc/NetworkManager/system-connections/br0.nmconnection
    permissions: '0600'
    content: |
      [connection]
      id=br0
      type=bridge
      interface-name=br0
      autoconnect=true
      autoconnect-priority=100

      [bridge]
      stp=false

      [ipv4]
      method=auto
      link-local=fallback
      may-fail=true

      [ipv6]
      method=link-local

  # The Ethernet port, as a port of the bridge.
  - path: /etc/NetworkManager/system-connections/eth0-port.nmconnection
    permissions: '0600'
    content: |
      [connection]
      id=eth0-port
      type=ethernet
      interface-name=eth0
      master=br0
      slave-type=bridge
      autoconnect=true
      autoconnect-priority=100

  # The access point, also a port of the bridge. WPA2-PSK with CCMP only
  # and no management-frame protection: the plainest combination, which
  # is what an ESP32 such as the FujiNet's joins without fuss.
  - path: /etc/NetworkManager/system-connections/$WIFI_SSID.nmconnection
    permissions: '0600'
    content: |
      [connection]
      id=$WIFI_SSID
      type=wifi
      interface-name=wlan0
      master=br0
      slave-type=bridge
      autoconnect=true
      autoconnect-priority=100

      [wifi]
      mode=ap
      ssid=$WIFI_SSID
      band=bg
      channel=$WIFI_CHANNEL
      powersave=2

      [wifi-security]
      key-mgmt=wpa-psk
      proto=rsn;
      pairwise=ccmp;
      group=ccmp;
      pmf=1
      psk=$WIFI_PSK

runcmd:
  - [ raspi-config, nonint, do_wifi_country, $WIFI_COUNTRY ]
  - [ raspi-config, nonint, do_ssh, 0 ]
  - [ rfkill, unblock, wifi ]
  - [ nmcli, connection, reload ]

# One clean start with the profiles in place before anything is asked of it.
power_state:
  mode: reboot
  message: $WIFI_SSID bridge configured, rebooting
  timeout: 30
  condition: true
EOF

# The network is entirely in the profiles above; cloud-init writes none.
cat > "$BOOT/network-config" <<'EOF'
# The WOODHAVEN bridge's network is defined by the NetworkManager profiles
# in user-data, not here.
network:
  config: disabled
EOF

# The stock sshswitch service turns SSH on when this file exists.
: > "$BOOT/ssh"

# One line. Keep what the stock image put there; add the Wi-Fi country so
# the radio is not blocked before the country is set.
CMDLINE="$BOOT/cmdline.txt"
if ! tr ' ' '\n' < "$CMDLINE" | grep -q '^cfg80211.ieee80211_regdom='; then
  printf '%s cfg80211.ieee80211_regdom=%s\n' "$(tr -d '\n' < "$CMDLINE")" "$WIFI_COUNTRY" > "$CMDLINE.new"
  mv "$CMDLINE.new" "$CMDLINE"
fi

echo "--- cmdline.txt"; cat "$CMDLINE"
echo "--- user-data"; sed "s|$WIFI_PSK|(psk)|; s|$HASH|(hash)|" "$BOOT/user-data"
ls -l "$BOOT/user-data" "$BOOT/network-config" "$BOOT/ssh"

# ------------------------------------------------------------------ close --
log "Unmounting"
sync
cleanup
trap - EXIT
DEV=

log "Done"
ls -lh "$IMG"
shasum -a 256 "$IMG" | tee "$IMG.sha256"
