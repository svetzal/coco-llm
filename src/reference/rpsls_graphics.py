"""CG6 assets and independent framebuffer oracle for the graphical hand game."""

from pathlib import Path

from PIL import Image

WIDTH, HEIGHT = 128, 192
SPRITE_WIDTH, SPRITE_HEIGHT = 48, 72
PALETTE = ((48, 216, 64), (232, 232, 48), (56, 72, 216), (232, 72, 56))
# Public keys are in the name order; the established engine uses cyclic order.
KEY_MOVES = (0, 2, 4, 3, 1)
NAMES = ("ROCK", "SPOCK", "PAPER", "LIZARD", "SCISSORS")
# Three ink pixels and a blank column. Five rows, each doubled vertically.
GLYPHS = {
    " ": "000 000 000 000 000",
    "0": "111 101 101 101 111",
    "1": "010 110 010 010 111",
    "2": "110 001 010 100 111",
    "3": "110 001 010 001 110",
    "4": "101 101 111 001 001",
    "5": "111 100 110 001 110",
    "6": "011 100 111 101 111",
    "7": "111 001 010 010 010",
    "8": "111 101 111 101 111",
    "9": "111 101 111 001 110",
    "A": "010 101 111 101 101",
    "B": "110 101 110 101 110",
    "C": "011 100 100 100 011",
    "D": "110 101 101 101 110",
    "E": "111 100 110 100 111",
    "F": "111 100 110 100 100",
    "G": "011 100 101 101 011",
    "H": "101 101 111 101 101",
    "I": "111 010 010 010 111",
    "J": "001 001 001 101 010",
    "K": "101 101 110 101 101",
    "L": "100 100 100 100 111",
    "M": "101 111 111 101 101",
    "N": "101 111 111 111 101",
    "O": "010 101 101 101 010",
    "P": "110 101 110 100 100",
    "Q": "010 101 101 111 011",
    "R": "110 101 110 101 101",
    "S": "011 100 010 001 110",
    "T": "111 010 010 010 010",
    "U": "101 101 101 101 111",
    "V": "101 101 101 101 010",
    "W": "101 101 111 111 101",
    "X": "101 101 010 101 101",
    "Y": "101 101 010 010 010",
    "Z": "111 001 010 100 111",
    "?": "110 001 010 000 010",
}


def pack(pixels: list[int]) -> bytes:
    if len(pixels) % 4 or any(p not in range(4) for p in pixels):
        raise ValueError("CG6 needs groups of four two-bit pixels")
    return bytes(
        sum(pixels[i + j] << (6 - 2 * j) for j in range(4))
        for i in range(0, len(pixels), 4)
    )


def compile_sprites(source: Path) -> list[bytes]:
    """Compile the approved concept to 2-bpp, compensating for 2:1 pixels.

    This is build-time artwork conversion, never gameplay or learning.
    Green-column gaps separate the five illustrations in the source sheet.
    """
    sheet = Image.open(source).convert("RGB")
    mask = Image.new("1", sheet.size)
    mask.putdata([not (g > r * 1.25 and g > b * 1.25) for r, g, b in sheet.getdata()])
    spans, start = [], None
    for x in range(sheet.width + 1):
        occupied = x < sheet.width and mask.crop((x, 0, x + 1, sheet.height)).getbbox()
        if occupied and start is None:
            start = x
        if not occupied and start is not None:
            if x - start > 20:
                spans.append((start, x))
            start = None
    if len(spans) != 5:
        raise ValueError(f"expected five separated hands, found {spans}")
    result = [b""] * 5
    for move, (left, right) in zip(KEY_MOVES, spans, strict=True):
        bbox = mask.crop((left, 0, right, sheet.height)).getbbox()
        crop = sheet.crop((left, bbox[1], right, bbox[3]))
        scale = min(44 * 2 / crop.width, 68 / crop.height)
        w, h = max(1, round(crop.width * scale / 2)), max(1, round(crop.height * scale))
        small = crop.resize((w, h), Image.Resampling.NEAREST)
        pixels = [0] * (SPRITE_WIDTH * SPRITE_HEIGHT)
        x0, y0 = (SPRITE_WIDTH - w) // 2, (SPRITE_HEIGHT - h) // 2
        for y in range(h):
            for x in range(w):
                rgb = small.getpixel((x, y))
                colour = min(
                    range(4),
                    key=lambda c: sum(
                        (a - b) ** 2 for a, b in zip(rgb, PALETTE[c], strict=True)
                    ),
                )
                pixels[(y + y0) * SPRITE_WIDTH + x + x0] = colour
        result[move] = pack(pixels)
    return result


def font_bytes(ink: int, background: int) -> bytes:
    return b"".join(
        pack([ink if bit == "1" else background for bit in row] + [background])
        for code in range(32, 91)
        for row in GLYPHS.get(chr(code), GLYPHS["?"]).split()
    )


def render(
    sprites: list[bytes],
    player: int | None = None,
    computer: int | None = None,
    scores: tuple[int, int] = (0, 0),
    message: str = "PICK A HAND",
) -> bytes:
    frame = bytearray(6144)

    def text(value: str, column: int, y: int, bright: bool = False) -> None:
        font = font_bytes(1, 2) if bright else font_bytes(2, 0)
        for i, ch in enumerate(value):
            offset = (ord(ch) - 32) * 5
            for row in range(5):
                for repeat in range(2):
                    frame[(y + row * 2 + repeat) * 32 + column + i] = font[offset + row]

    def centred(
        value: str, y: int, start: int = 0, width: int = 32, bright: bool = False
    ) -> None:
        text(value, start + (width - len(value)) // 2, y, bright)

    centred("YOU", 2, 0, 16)
    centred("COCO", 2, 16, 16)
    for move, column in ((player, 2), (computer, 18)):
        if move is not None:
            for row in range(72):
                frame[(16 + row) * 32 + column : (16 + row) * 32 + column + 12] = (
                    sprites[move][row * 12 : row * 12 + 12]
                )
            centred(NAMES[move], 90, column - 2, 16)
        else:
            centred("?", 46, column - 2, 16)
    text(f"{scores[0]:03}", 6, 110)
    text(f"{scores[1]:03}", 22, 110)
    frame[136 * 32 : 150 * 32] = bytes([0xAA]) * (14 * 32)
    centred(message, 138, bright=True)
    centred("1 ROCK   2 PAPER", 154)
    centred("3 SCISSORS  4 LIZARD", 166)
    centred("5 SPOCK  R NEW GAME", 178)
    return bytes(frame)


def save_preview(frame: bytes, path: Path) -> None:
    image = Image.new("RGB", (128, 192))
    image.putdata(
        [PALETTE[(byte >> shift) & 3] for byte in frame for shift in (6, 4, 2, 0)]
    )
    image.resize((768, 576), Image.Resampling.NEAREST).save(path)
