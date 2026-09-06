#!/bin/bash
# Build the signage SD-card image from a stock Raspberry Pi OS Lite release.
#
# Runs inside the builder container (see Dockerfile), which must be started
# with --privileged. Expects:
#
#   /src    the signage/ directory, read-only
#   /work   the signage/build/ directory, where the image is written
#
# Steps, in order: fetch and verify the base image, grow it, mount both
# partitions through offset loop devices, lay the overlay files on top,
# customise the root filesystem in a native chroot (install fbi, create the
# user, enable the service), copy the slides in, edit the boot files, and
# unmount. The result is /work/coco-signage.img, ready to write to a card.
#
# `verify` as the first argument mounts a built image read-only and lists
# what the boot depends on, which is the most this Mac can check without a
# Pi.

set -euo pipefail

SRC=/src
WORK=/work
IMG="$WORK/coco-signage.img"
MNT=/mnt/root

# shellcheck source=../signage.conf
. "$SRC/signage.conf"

LOOP_BOOT=
LOOP_ROOT=
PRELOAD_MOVED=
RESOLV_MOVED=

log() { printf '\n==> %s\n' "$*"; }

cleanup() {
  set +e
  if mountpoint -q "$MNT"; then
    [ -n "$PRELOAD_MOVED" ] && mv "$MNT/etc/ld.so.preload.signage" "$MNT/etc/ld.so.preload"
    if [ -n "$RESOLV_MOVED" ]; then
      rm -f "$MNT/etc/resolv.conf"
      mv "$MNT/etc/resolv.conf.signage" "$MNT/etc/resolv.conf"
    fi
    rm -f "$MNT/usr/sbin/policy-rc.d" "$MNT/tmp/customize.sh" "$MNT/tmp/signage.conf"
    for dir in dev/pts dev proc sys boot/firmware; do
      mountpoint -q "$MNT/$dir" && umount -l "$MNT/$dir"
    done
    umount -l "$MNT"
  fi
  [ -n "$LOOP_BOOT" ] && losetup -d "$LOOP_BOOT"
  [ -n "$LOOP_ROOT" ] && losetup -d "$LOOP_ROOT"
  true
}
trap cleanup EXIT

# Sector start and size of partition N of the image, from sfdisk's dump.
part_field() {
  sfdisk -d "$IMG" | grep "^$IMG$1 " | sed -E "s/.*$2= *([0-9]+).*/\1/"
}

attach_loops() {
  local start size
  start=$(part_field 1 start); size=$(part_field 1 size)
  LOOP_BOOT=$(losetup -f --show -o $((start * 512)) --sizelimit $((size * 512)) "$IMG")
  start=$(part_field 2 start); size=$(part_field 2 size)
  LOOP_ROOT=$(losetup -f --show -o $((start * 512)) --sizelimit $((size * 512)) "$IMG")
  echo "boot partition on $LOOP_BOOT, root on $LOOP_ROOT"
}

mount_image() {
  local mode="$1"
  mkdir -p "$MNT"
  mount -o "$mode" "$LOOP_ROOT" "$MNT"
  mount -o "$mode" "$LOOP_BOOT" "$MNT/boot/firmware"
}

# ---------------------------------------------------------------- verify --
if [ "${1:-}" = verify ]; then
  [ -f "$IMG" ] || { echo "no image at $IMG; run make image first" >&2; exit 1; }
  attach_loops
  mount_image ro
  log "Root filesystem"
  df -h "$MNT" | tail -1
  log "Slides"
  ls "$MNT/opt/coco-signage/slides" | sed 's/^/  /'
  log "Service"
  cat "$MNT/etc/coco-signage.conf"
  ls -l "$MNT/etc/systemd/system/multi-user.target.wants/coco-signage.service"
  ls -l "$MNT/etc/systemd/system/getty@tty1.service"
  chroot "$MNT" /usr/bin/fbi --version 2>&1 | head -1
  chroot "$MNT" /usr/bin/fbi --help 2>&1 | grep -q -- '-blend' \
    && echo "fbi supports --blend; slides will fade" \
    || echo "fbi has no --blend; slides will cut"
  log "User"
  grep "^$SIGNAGE_USER:" "$MNT/etc/passwd"
  log "Boot files"
  cat "$MNT/boot/firmware/cmdline.txt"
  tail -n 5 "$MNT/boot/firmware/config.txt"
  exit 0
fi

# ------------------------------------------------------------------ fetch --
log "Base image"
mkdir -p "$WORK/base"
BASE_XZ="$WORK/base/$(basename "$BASE_IMAGE_URL")"
if [ ! -f "$BASE_XZ" ]; then
  echo "downloading $BASE_IMAGE_URL"
  curl -fL --progress-bar -o "$BASE_XZ.part" "$BASE_IMAGE_URL"
  mv "$BASE_XZ.part" "$BASE_XZ"
fi
echo "$BASE_IMAGE_SHA256  $BASE_XZ" | sha256sum -c -

log "Decompressing"
rm -f "$IMG"
xz -dc -T0 "$BASE_XZ" > "$IMG"

# ------------------------------------------------------------------- grow --
log "Growing the root partition by ${GROW_MB} MB"
truncate -s +"${GROW_MB}M" "$IMG"
echo ", +" | sfdisk -q -N 2 --no-reread --no-tell-kernel "$IMG"
attach_loops
e2fsck -fp "$LOOP_ROOT" >/dev/null
resize2fs "$LOOP_ROOT" 2>&1 | tail -1

# ------------------------------------------------------------------ mount --
log "Mounting"
mount_image rw
df -h "$MNT" | tail -1

# ---------------------------------------------------------------- overlay --
log "Overlay files"
tar -C "$SRC/image/rootfs" -cf - . | tar -C "$MNT" --no-same-owner -xf -
chmod 755 "$MNT/usr/local/bin/coco-signage"
chmod 644 "$MNT/etc/systemd/system/coco-signage.service"

log "Slides"
[ -n "$(ls "$WORK/slides/"*.png 2>/dev/null)" ] || { echo "no rendered slides in $WORK/slides; run make slides first" >&2; exit 1; }
mkdir -p "$MNT/opt/coco-signage/slides"
cp "$WORK/slides/"*.png "$MNT/opt/coco-signage/slides/"
chmod 644 "$MNT/opt/coco-signage/slides/"*.png
ls "$MNT/opt/coco-signage/slides" | wc -l | sed 's/$/ slides/'

cat > "$MNT/etc/coco-signage.conf" <<EOF
# Written by the image builder from signage/signage.conf.
SLIDE_SECONDS=$SLIDE_SECONDS
BLEND_MS=$BLEND_MS
FBI_DEVICE=$FBI_DEVICE
EOF

# ----------------------------------------------------------------- chroot --
log "Customising the root filesystem"
# The Pi's ld.so.preload names a memory library that does not exist on
# this host; every binary in the chroot would complain. Move it aside.
if [ -f "$MNT/etc/ld.so.preload" ]; then
  mv "$MNT/etc/ld.so.preload" "$MNT/etc/ld.so.preload.signage"; PRELOAD_MOVED=1
fi
# The image's resolv.conf points at NetworkManager; give apt a real one.
if [ -e "$MNT/etc/resolv.conf" ] || [ -L "$MNT/etc/resolv.conf" ]; then
  mv "$MNT/etc/resolv.conf" "$MNT/etc/resolv.conf.signage"; RESOLV_MOVED=1
fi
cp /etc/resolv.conf "$MNT/etc/resolv.conf"
# Stop package installs from trying to start services in the chroot.
printf '#!/bin/sh\nexit 101\n' > "$MNT/usr/sbin/policy-rc.d"
chmod 755 "$MNT/usr/sbin/policy-rc.d"

mount --bind /dev "$MNT/dev"
mount --bind /dev/pts "$MNT/dev/pts"
mount -t proc proc "$MNT/proc"
mount -t sysfs sys "$MNT/sys"

cp "$SRC/image/customize.sh" "$MNT/tmp/customize.sh"
cp "$SRC/signage.conf" "$MNT/tmp/signage.conf"
chroot "$MNT" /bin/bash /tmp/customize.sh

# ------------------------------------------------------------- boot files --
log "Boot files"
BOOT="$MNT/boot/firmware"
CMDLINE="$BOOT/cmdline.txt"
# One line. Keep everything the stock image put there, including the
# first-boot init that grows the partition; add the console quieting.
add_cmdline() {
  local key="${1%%=*}"
  if ! tr ' ' '\n' < "$CMDLINE" | grep -q "^$key\(=\|$\)"; then
    printf '%s %s\n' "$(tr -d '\n' < "$CMDLINE")" "$1" > "$CMDLINE.new"
    mv "$CMDLINE.new" "$CMDLINE"
  fi
}
add_cmdline consoleblank=0
add_cmdline logo.nologo
add_cmdline vt.global_cursor_default=0
add_cmdline loglevel=3
if [ -n "$WIFI_COUNTRY" ]; then
  add_cmdline "cfg80211.ieee80211_regdom=$WIFI_COUNTRY"
fi
cat "$CMDLINE"

if ! grep -q "coco-signage" "$BOOT/config.txt"; then
  cat >> "$BOOT/config.txt" <<'EOF'

# coco-signage: no boot splash. If the TV shows nothing or the wrong
# size, force a mode by adding to cmdline.txt (one line, space-separated):
#   video=HDMI-A-1:1920x1080@60
[all]
disable_splash=1
EOF
fi

# ------------------------------------------------------------------ close --
log "Unmounting"
sync
cleanup
trap - EXIT
LOOP_BOOT=; LOOP_ROOT=

log "Done"
ls -lh "$IMG"
sha256sum "$IMG" | tee "$IMG.sha256"
