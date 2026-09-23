#!/usr/bin/env python3
"""Build the README interaction preview from the same portraits used by the demo."""

from __future__ import annotations

import io
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "assets" / "draggable-card-stack.gif"
SIZE = (800, 450)
CARD_SIZE = (188, 244)
CARD_CENTER = (588, 232)
BACKGROUND = "#f2eee8"

PEOPLE = [
    ("Maya Chen", "CREATIVE DIRECTOR", "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=650&q=82"),
    ("Jon Bell", "DESIGN LEAD", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=650&q=82"),
    ("Aisha Reed", "BRAND STRATEGIST", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=650&q=82"),
    ("Leo Martin", "MOTION DESIGNER", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=650&q=82"),
    ("Nora Kim", "PRODUCER", "https://images.unsplash.com/photo-1551836022-d5d88e9218df?auto=format&fit=crop&w=650&q=82"),
]

BASE_X = [0, 11, -12, 19, -20]
BASE_Y = [0, 5, 9, 14, 19]
BASE_ROTATION = [0, 4, -5, 7, -8]


def font(size: int, serif: bool = False) -> ImageFont.ImageFont:
    candidates = (
        ["/System/Library/Fonts/NewYork.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"]
        if serif
        else ["/System/Library/Fonts/HelveticaNeue.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def ease(value: float) -> float:
    return 1 - (1 - value) ** 3


def load_portraits() -> list[Image.Image]:
    portraits = []
    for _, _, url in PEOPLE:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            image = Image.open(io.BytesIO(response.read())).convert("RGB")
        portraits.append(ImageOps.fit(image, CARD_SIZE, method=Image.Resampling.LANCZOS))
    return portraits


def make_card(index: int, portrait: Image.Image) -> Image.Image:
    width, height = CARD_SIZE
    radius = 16
    card = Image.new("RGBA", CARD_SIZE, (0, 0, 0, 0))
    mask = Image.new("L", CARD_SIZE, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, height - 1), radius=radius, fill=255)
    card.paste(portrait, (0, 0), mask)

    shade = Image.new("RGBA", CARD_SIZE, (0, 0, 0, 0))
    shade_pixels = shade.load()
    for y in range(height):
        opacity = int(max(0, (y / height - 0.55) / 0.45) * 175)
        for x in range(width):
            shade_pixels[x, y] = (10, 10, 9, opacity)
    card.alpha_composite(shade)

    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle((1, 1, width - 2, height - 2), radius=radius, outline="#faf8f3", width=3)
    draw.text((12, 11), f"{index + 1:02d} / 05", fill="white", font=font(7))
    draw.text((12, height - 43), PEOPLE[index][1], fill="white", font=font(7))
    draw.text((12, height - 29), PEOPLE[index][0], fill="white", font=font(15))
    return card


def composite_card(canvas: Image.Image, card: Image.Image, x: float, y: float, rotation: float, scale: float) -> None:
    transformed = card.resize(
        (int(card.width * scale), int(card.height * scale)),
        Image.Resampling.LANCZOS,
    ).rotate(-rotation, resample=Image.Resampling.BICUBIC, expand=True)
    left = int(CARD_CENTER[0] - transformed.width / 2 + x)
    top = int(CARD_CENTER[1] - transformed.height / 2 + y)
    shadow = Image.new("RGBA", transformed.size, (0, 0, 0, 0))
    shadow.putalpha(transformed.getchannel("A").point(lambda value: value * 35 // 255))
    canvas.alpha_composite(shadow, (left + 5, top + 8))
    canvas.alpha_composite(transformed, (left, top))


def base_frame() -> Image.Image:
    canvas = Image.new("RGBA", SIZE, BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((52, 34, 62, 44), fill="#1b1b19")
    draw.text((70, 31), "Atelier", fill="#1b1b19", font=font(12))
    draw.ellipse((53, 83, 59, 89), fill="#d8ff43", outline="#1b1b19", width=1)
    draw.text((68, 79), "THE PEOPLE BEHIND THE WORK", fill="#1b1b19", font=font(7))
    draw.text((52, 112), "Small team.", fill="#1b1b19", font=font(50))
    draw.text((52, 162), "Big energy.", fill="#1b1b19", font=font(49, serif=True))
    draw.text((53, 368), "DRAG TO EXPLORE   >", fill="#77736d", font=font(8))
    draw.text((53, 405), "Mouse · Touch · Keyboard", fill="#77736d", font=font(8))
    return canvas


def render_stack(
    cards: list[Image.Image],
    order: list[int],
    moving: tuple[int, float, float, float, float] | None = None,
    moved_to_back: bool = False,
) -> Image.Image:
    canvas = base_frame()
    positions: dict[int, tuple[float, float, float, float]] = {}
    for position, card_index in enumerate(order):
        positions[card_index] = (
            BASE_X[position],
            BASE_Y[position],
            BASE_ROTATION[position],
            1 - position * 0.022,
        )
    if moving:
        card_index, x, y, rotation, scale = moving
        positions[card_index] = (x, y, rotation, scale)

    draw_order = list(reversed(order))
    if moving and not moved_to_back:
        moving_index = moving[0]
        draw_order.remove(moving_index)
        draw_order.append(moving_index)

    for card_index in draw_order:
        composite_card(canvas, cards[card_index], *positions[card_index])
    return canvas.convert("RGB")


def animate_cycle(cards: list[Image.Image], order: list[int], direction: int) -> tuple[list[Image.Image], list[int]]:
    frames = [render_stack(cards, order) for _ in range(5)]
    moving_index = order[0]

    for step in range(1, 8):
        progress = ease(step / 7)
        frames.append(
            render_stack(
                cards,
                order,
                (moving_index, direction * 92 * progress, 8 * progress, direction * 9 * progress, 1 - 0.025 * progress),
            )
        )

    new_order = order[1:] + [moving_index]
    for step in range(1, 10):
        progress = ease(step / 9)
        x = direction * (92 * (1 - progress)) + BASE_X[-1] * progress
        y = 8 * (1 - progress) + BASE_Y[-1] * progress
        rotation = direction * 9 * (1 - progress) + BASE_ROTATION[-1] * progress
        scale = 0.975 * (1 - progress) + (1 - 4 * 0.022) * progress
        frames.append(render_stack(cards, new_order, (moving_index, x, y, rotation, scale), moved_to_back=True))

    frames.extend(render_stack(cards, new_order) for _ in range(5))
    return frames, new_order


def main() -> None:
    portraits = load_portraits()
    cards = [make_card(index, portrait) for index, portrait in enumerate(portraits)]
    order = list(range(len(cards)))
    frames, order = animate_cycle(cards, order, 1)
    second_frames, _ = animate_cycle(cards, order, -1)
    frames.extend(second_frames)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        duration=65,
        loop=0,
        optimize=True,
    )
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
