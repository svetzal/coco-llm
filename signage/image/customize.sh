#!/bin/bash
# Runs INSIDE the chroot of the Raspberry Pi OS root filesystem, natively
# on arm64. Called by build-image.sh; not meant to be run by hand.
#
# Everything a stock Lite image needs to become a slideshow that starts
# itself: the image viewer, a user so the first-boot wizard does not stop
# on the console and wait for one, the service enabled, the login prompt
# on the display retired, and optional SSH and Wi-Fi for updating slides
# in the field.

set -euo pipefail

# shellcheck source=../signage.conf
. /tmp/signage.conf

export DEBIAN_FRONTEND=noninteractive

echo "--- packages"
apt-get update -qq
# fbi draws PNGs straight onto the display from a console. No desktop, no
# browser, no window manager: it is the whole of the display stack.
apt-get install -y -qq --no-install-recommends fbi
apt-get clean
rm -rf /var/lib/apt/lists/*
dpkg -s fbi | grep -E '^(Package|Version):'

echo "--- user $SIGNAGE_USER"
# The stock image ships a placeholder user, pi, with no login shell, and a
# first-boot wizard that renames it and sets a password from the console.
# Left alone, that wizard would sit on the display waiting for a keyboard.
# The image's own userconf script is what the wizard (and Raspberry Pi
# Imager's settings) call to finish the job, so call it here with a
# hashed password; it renames pi, sets the shell, and cancels the wizard.
HASH=$(openssl passwd -6 "$SIGNAGE_PASSWORD")
/usr/lib/userconf-pi/userconf "$SIGNAGE_USER" "$HASH"
for group in adm dialout cdrom sudo audio video plugdev games users input render netdev gpio i2c spi; do
  getent group "$group" >/dev/null && usermod -aG "$group" "$SIGNAGE_USER"
done
systemctl disable userconfig.service 2>/dev/null || true
grep "^$SIGNAGE_USER:" /etc/passwd

echo "--- identity"
echo "$SIGNAGE_HOSTNAME" > /etc/hostname
sed -i "s/^127\.0\.1\.1.*/127.0.1.1\t$SIGNAGE_HOSTNAME/" /etc/hosts
grep -q "^127.0.1.1" /etc/hosts || printf '127.0.1.1\t%s\n' "$SIGNAGE_HOSTNAME" >> /etc/hosts
ln -sf "/usr/share/zoneinfo/$TIMEZONE" /etc/localtime
echo "$TIMEZONE" > /etc/timezone

echo "--- services"
# The slideshow owns tty1. The login prompt that normally lives there is
# masked, not merely disabled, so nothing can pull it back.
systemctl enable coco-signage.service
systemctl mask getty@tty1.service
if [ "$ENABLE_SSH" = yes ]; then
  systemctl enable ssh.service
  # Host keys are generated on first boot by the stock image's own service.
fi

if [ -n "$WIFI_SSID" ]; then
  echo "--- wi-fi $WIFI_SSID"
  install -d -m 700 /etc/NetworkManager/system-connections
  cat > /etc/NetworkManager/system-connections/signage.nmconnection <<EOF
[connection]
id=signage
type=wifi
autoconnect=true

[wifi]
mode=infrastructure
ssid=$WIFI_SSID

[wifi-security]
key-mgmt=wpa-psk
psk=$WIFI_PSK

[ipv4]
method=auto

[ipv6]
method=auto
EOF
  chmod 600 /etc/NetworkManager/system-connections/signage.nmconnection
fi

echo "--- done"
