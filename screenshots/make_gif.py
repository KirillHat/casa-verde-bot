"""Compose demo.gif from the four PNG mockups.

Run:
    python screenshots/make_gif.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
FRAMES = ["01_whatsapp_es.png", "02_whatsapp_en.png", "03_sheet.png", "04_slack.png"]

CANVAS = (1200, 800)
BG = (243, 244, 246, 255)  # gray-100
FRAME_DURATION_MS = 2200  # ~2.2s per frame


def fit_into_canvas(img: Image.Image) -> Image.Image:
    canvas = Image.new("RGBA", CANVAS, BG)
    img = img.convert("RGBA")
    scale = min(CANVAS[0] / img.width, CANVAS[1] / img.height) * 0.92
    new_size = (int(img.width * scale), int(img.height * scale))
    resized = img.resize(new_size, Image.LANCZOS)
    x = (CANVAS[0] - new_size[0]) // 2
    y = (CANVAS[1] - new_size[1]) // 2
    canvas.paste(resized, (x, y), resized)
    return canvas.convert("P", palette=Image.ADAPTIVE)


def main() -> None:
    frames = [fit_into_canvas(Image.open(HERE / f)) for f in FRAMES]
    out = HERE / "demo.gif"
    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=True,
    )
    print(f"✓ {out.name} ({out.stat().st_size // 1024} KB, {len(frames)} frames)")


if __name__ == "__main__":
    main()
