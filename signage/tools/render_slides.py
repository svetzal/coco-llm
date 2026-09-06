"""Render the signage slides to PNG, one file per slide, at 1920 by 1080.

The Raspberry Pi shows PNGs rather than running a browser: there is no
desktop to start, nothing to crash, and the boot is a few seconds. So the
slides are authored as HTML here, where the deck's palette and typeface
already live, and rendered on the Mac with headless Chrome.

The page is served over a local HTTP server during rendering rather than
opened as a file, because Chrome refuses to load a web font from file://
and Hot CoCo is the point of the look.

Output: signage/build/slides/NN.png, numbered in slide order.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SLIDES_HTML = ROOT / "signage" / "slides" / "index.html"
OUTPUT_DIR = ROOT / "signage" / "build" / "slides"
WIDTH, HEIGHT = 1920, 1080

CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
    "chromium-browser",
)


def find_chrome() -> str:
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
        found = shutil.which(candidate)
        if found:
            return found
    sys.exit("No Chrome or Chromium found; install Google Chrome to render slides.")


def count_slides() -> int:
    html = SLIDES_HTML.read_text()
    return len(re.findall(r"<section\b", html))


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:  # noqa: D401 - silence per-request logs
        pass


def serve_root() -> tuple[http.server.ThreadingHTTPServer, int]:
    handler = functools.partial(QuietHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, server.server_address[1]


def render(chrome: str, port: int, index: int, profile: Path) -> Path:
    out = OUTPUT_DIR / f"{index:02d}.png"
    url = f"http://127.0.0.1:{port}/signage/slides/index.html?slide={index}"
    command = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={profile}",
        f"--window-size={WIDTH},{HEIGHT}",
        "--force-device-scale-factor=1",
        # Let fonts and the data script settle before the shot.
        "--virtual-time-budget=4000",
        f"--screenshot={out}",
        url,
    ]
    # Chrome writes the screenshot and then, on this Mac, never exits. So
    # watch for the file rather than for the process: once it exists and
    # has stopped growing, the shot is done and Chrome can be closed.
    out.unlink(missing_ok=True)
    process = subprocess.Popen(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:
        deadline = time.monotonic() + 60
        last_size = -1
        while time.monotonic() < deadline:
            if out.is_file():
                size = out.stat().st_size
                if size and size == last_size:
                    return out
                last_size = size
            elif process.poll() is not None:
                break
            time.sleep(0.25)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    sys.exit(f"Chrome produced no screenshot for slide {index}")


def check_size(path: Path) -> None:
    try:
        from PIL import Image
    except ImportError:
        return
    with Image.open(path) as image:
        if image.size != (WIDTH, HEIGHT):
            sys.exit(f"{path.name} is {image.size}, expected {(WIDTH, HEIGHT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", type=int, help="render one slide number")
    arguments = parser.parse_args()

    chrome = find_chrome()
    total = count_slides()
    if total == 0:
        sys.exit(f"No <section> slides in {SLIDES_HTML}")

    if arguments.only is None:
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    server, port = serve_root()
    try:
        with tempfile.TemporaryDirectory(prefix="signage-chrome-") as profile:
            wanted = [arguments.only] if arguments.only else range(1, total + 1)
            for index in wanted:
                path = render(chrome, port, index, Path(profile))
                check_size(path)
                print(f"slide {index:2d}/{total}  {path.relative_to(ROOT)}")
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
