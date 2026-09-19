"""Print the on-screen rectangle of the XRoar window as x,y,w,h in screen points.

Asks the window server, which needs no Accessibility permission. Run with
pyobjc's Quartz binding available, e.g.

    uv run --with pyobjc-framework-Quartz python tools/xroar_window.py

Exits 1 if no XRoar window is on screen.
"""

from __future__ import annotations

import sys

import Quartz


def main() -> int:
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID,
    )
    for window in windows:
        owner = str(window.get("kCGWindowOwnerName", ""))
        if "xroar" not in owner.lower() or window.get("kCGWindowLayer", 1) != 0:
            continue
        b = window["kCGWindowBounds"]
        print(f"{int(b['X'])},{int(b['Y'])},{int(b['Width'])},{int(b['Height'])}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
