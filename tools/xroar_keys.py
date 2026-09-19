"""Type into the XRoar window: click it so it is the key window, then post
hardware-style key events, which the SDL window sees as real keystrokes.

    uv run --with pyobjc-framework-Quartz python tools/xroar_keys.py X,Y,W,H TEXT

TEXT is typed character by character. Named keys go in braces: {return},
{space}, {up}, {down}, {left}, {right}, {esc}, {tab}, {backspace}. Letters are
sent lower-case; XRoar maps them to the CoCo's keys. Needs Accessibility
permission for the process posting the events.
"""

from __future__ import annotations

import re
import sys
import time

import Quartz

KEYCODES = {
    "a": 0, "s": 1, "d": 2, "f": 3, "h": 4, "g": 5, "z": 6, "x": 7, "c": 8, "v": 9,
    "b": 11, "q": 12, "w": 13, "e": 14, "r": 15, "y": 16, "t": 17, "1": 18, "2": 19,
    "3": 20, "4": 21, "6": 22, "5": 23, "=": 24, "9": 25, "7": 26, "-": 27, "8": 28,
    "0": 29, "]": 30, "o": 31, "u": 32, "[": 33, "i": 34, "p": 35, "l": 37, "j": 38,
    "'": 39, "k": 40, ";": 41, "\\": 42, ",": 43, "/": 44, "n": 45, "m": 46, ".": 47,
    "`": 50, " ": 49,
    "{space}": 49, "{return}": 36, "{tab}": 48, "{backspace}": 51, "{esc}": 53,
    "{left}": 123, "{right}": 124, "{down}": 125, "{up}": 126,
}
SHIFTED = {"!": "1", "@": "2", "#": "3", "$": "4", "%": "5", "^": "6", "&": "7",
           "*": "8", "(": "9", ")": "0", "?": "/", ":": ";", '"': "'", "+": "=",
           "<": ",", ">": ".", "_": "-"}


def post(event) -> None:
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def click(x: int, y: int) -> None:
    for kind in (Quartz.kCGEventLeftMouseDown, Quartz.kCGEventLeftMouseUp):
        post(Quartz.CGEventCreateMouseEvent(None, kind, (x, y), Quartz.kCGMouseButtonLeft))
        time.sleep(0.05)


def press(code: int, shift: bool = False) -> None:
    down = Quartz.CGEventCreateKeyboardEvent(None, code, True)
    up = Quartz.CGEventCreateKeyboardEvent(None, code, False)
    if shift:
        Quartz.CGEventSetFlags(down, Quartz.kCGEventFlagMaskShift)
        Quartz.CGEventSetFlags(up, Quartz.kCGEventFlagMaskShift)
    post(down)
    time.sleep(0.06)
    post(up)
    time.sleep(0.08)


def main() -> int:
    x, y, w, h = map(int, sys.argv[1].split(","))
    text = sys.argv[2]
    click(x + w // 2, y + h // 2)
    time.sleep(0.3)
    for token in re.findall(r"\{[a-z]+\}|.", text, flags=re.S):
        key = token.lower()
        shift = False
        if key in SHIFTED:
            key, shift = SHIFTED[key], True
        elif len(token) == 1 and token.isalpha() and token.isupper():
            shift = True
        if key not in KEYCODES:
            print(f"no key code for {token!r}", file=sys.stderr)
            return 1
        press(KEYCODES[key], shift)
    return 0


if __name__ == "__main__":
    sys.exit(main())
