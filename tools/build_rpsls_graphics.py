"""Compile the approved hand artwork and bitmap font for the 6809 build."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/reference"))
from rpsls_graphics import compile_sprites, font_bytes, render, save_preview


def main() -> None:
    output = ROOT / "build/exp019"
    output.mkdir(parents=True, exist_ok=True)
    sprites = compile_sprites(ROOT / "assets/rpsls/hand-concept.png")
    (output / "hands.bin").write_bytes(b"".join(sprites))
    (output / "font.bin").write_bytes(font_bytes(2, 0))
    (output / "font-bright.bin").write_bytes(font_bytes(1, 2))
    save_preview(render(sprites, 4, 2, (7, 3), "YOU WIN"), output / "reference.png")


if __name__ == "__main__":
    main()
