"""Print the on-screen rectangle of the XRoar window as x,y,w,h in screen points.

Asks the window server, which needs no Accessibility permission. Run with
pyobjc's Quartz binding available, e.g.

    uv run --with pyobjc-framework-Quartz python tools/xroar_window.py

Exits 1 if no XRoar window is on screen.
"""

from __future__ import annotations

import subprocess
import sys

import Quartz


def xroar_pids() -> set[int]:
    result = subprocess.run(["pgrep", "-x", "xroar"], capture_output=True, text=True)
    return {int(line) for line in result.stdout.split()}


def main() -> int:
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID,
    )
    pids = xroar_pids()
    for window in windows:
        # The owner name is the launching app's when XRoar is started from a
        # shell inside one (it reads "Claude" or "Terminal"), so match the
        # process id and fall back to the name.
        owner = str(window.get("kCGWindowOwnerName", ""))
        ours = window.get("kCGWindowOwnerPID") in pids or "xroar" in owner.lower()
        if not ours or window.get("kCGWindowLayer", 1) != 0:
            continue
        b = window["kCGWindowBounds"]
        print(f"{int(b['X'])},{int(b['Y'])},{int(b['Width'])},{int(b['Height'])}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
