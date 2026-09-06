# Tooling for building the signage image on a Mac.
#
# The base image is an arm64 Raspberry Pi OS, and this Mac is arm64, so the
# customisation runs in a native chroot with no emulation. The container
# exists to supply a Linux kernel: loop devices, ext4 and a chroot are
# things macOS cannot do. It must be run --privileged for the loop mounts.
#
# The build scripts are not copied in. They are mounted from signage/ at
# run time, so editing one does not need an image rebuild.

FROM debian:trixie

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates curl xz-utils \
      fdisk util-linux mount e2fsprogs dosfstools \
 && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/bin/bash", "/src/image/build-image.sh"]
