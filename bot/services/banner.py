from __future__ import annotations

import colorsys
from io import BytesIO

from PIL import Image, ImageDraw

from services.fonts import load_font

BANNER_SIZE = (1024, 400)
DEFAULT_ACCENT = (88, 101, 242)


def _vivid(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    r, g, b = (channel / 255 for channel in rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    s = max(s, 0.55)
    v = min(max(v, 0.5), 0.82)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return tuple(int(channel * 255) for channel in (r, g, b))  # type: ignore[return-value]


def accent_from_image(data: bytes | None) -> tuple[int, int, int]:
    """Compute a vivid accent color from image bytes (guild icon)."""
    if not data:
        return DEFAULT_ACCENT
    try:
        with Image.open(BytesIO(data)) as source:
            image = source.convert("RGB")
    except Exception:  # noqa: BLE001 - bad image should not break welcome flow
        return DEFAULT_ACCENT
    image = image.resize((32, 32), Image.Resampling.LANCZOS)
    pixels = list(image.getdata())
    if not pixels:
        return DEFAULT_ACCENT
    average = tuple(sum(pixel[i] for pixel in pixels) // len(pixels) for i in range(3))
    return _vivid(average)  # type: ignore[arg-type]


def _gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    width, height = size
    image = Image.new("RGB", size, bottom)
    draw = ImageDraw.Draw(image)
    span = max(height - 1, 1)
    for y in range(height):
        ratio = y / span
        color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)
    return image.convert("RGBA")


def _avatar(data: bytes | None, size: int, initial: str) -> Image.Image:
    image: Image.Image | None = None
    if data:
        try:
            with Image.open(BytesIO(data)) as source:
                image = source.convert("RGB").resize((size, size), Image.Resampling.LANCZOS)
        except Exception:  # noqa: BLE001
            image = None
    if image is None:
        image = Image.new("RGB", (size, size), (54, 58, 82))
        draw = ImageDraw.Draw(image)
        draw.text(
            (size / 2, size / 2),
            (initial or "?").upper()[:1],
            font=load_font(int(size * 0.45), bold=True),
            fill=(236, 238, 248),
            anchor="mm",
        )

    supersample = 4
    mask = Image.new("L", (size * supersample, size * supersample), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * supersample, size * supersample), fill=255)
    mask = mask.resize((size, size), Image.Resampling.LANCZOS)

    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(image, (0, 0), mask)
    return output


def _fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, size: int, *, bold: bool, minimum: int = 24):
    while size > minimum:
        font = load_font(size, bold=bold)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 2
    return load_font(minimum, bold=bold)


def _ellipsize(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> str:
    if draw.textlength(text, font=font) <= max_width:
        return text
    ellipsis = "..."
    trimmed = text
    while trimmed and draw.textlength(trimmed + ellipsis, font=font) > max_width:
        trimmed = trimmed[:-1]
    return (trimmed.rstrip() + ellipsis) if trimmed else ellipsis


def render_banner(
    *,
    display_name: str,
    subtitle: str = "",
    footer: str = "",
    server_name: str = "",
    avatar_bytes: bytes | None = None,
    accent: tuple[int, int, int] | None = None,
    initial: str = "?",
    size: tuple[int, int] = BANNER_SIZE,
) -> bytes:
    """Render a welcome banner PNG and return its bytes."""
    width, height = size
    top = accent or DEFAULT_ACCENT
    background = _gradient(size, top, (13, 15, 24))

    panel = Image.new("RGBA", size, (0, 0, 0, 0))
    panel_draw = ImageDraw.Draw(panel)
    panel_draw.rounded_rectangle(
        (32, 28, width - 32, height - 28),
        radius=36,
        fill=(8, 10, 18, 150),
        outline=(255, 255, 255, 30),
        width=1,
    )
    background = Image.alpha_composite(background, panel)
    draw = ImageDraw.Draw(background)

    avatar_size = 200
    avatar_x, avatar_y = 84, (height - avatar_size) // 2
    avatar = _avatar(avatar_bytes, avatar_size, initial)
    background.alpha_composite(avatar, (avatar_x, avatar_y))
    draw.ellipse(
        (avatar_x, avatar_y, avatar_x + avatar_size, avatar_y + avatar_size),
        outline=(255, 255, 255, 235),
        width=6,
    )

    text_x = avatar_x + avatar_size + 48
    max_text_width = width - text_x - 64

    if server_name:
        server_font = load_font(24, bold=False)
        server_text = _ellipsize(draw, server_name, server_font, 320)
        draw.text(
            (width - 64, 56),
            server_text,
            font=server_font,
            fill=(255, 255, 255, 185),
            anchor="ra",
        )

    name = display_name or "New member"
    name_font = _fit_font(draw, name, max_text_width, 62, bold=True, minimum=30)
    name = _ellipsize(draw, name, name_font, max_text_width)
    draw.text((text_x, 108), name, font=name_font, fill=(255, 255, 255, 255))

    if subtitle:
        subtitle_font = _fit_font(draw, subtitle, max_text_width, 30, bold=False, minimum=20)
        subtitle = _ellipsize(draw, subtitle, subtitle_font, max_text_width)
        draw.text((text_x, 200), subtitle, font=subtitle_font, fill=(226, 230, 244, 240))

    if footer:
        footer_font = _fit_font(draw, footer, max_text_width, 24, bold=False, minimum=16)
        footer = _ellipsize(draw, footer, footer_font, max_text_width)
        draw.text((text_x, 264), footer, font=footer_font, fill=(196, 202, 222, 220))

    output = BytesIO()
    background.convert("RGB").save(output, format="PNG", optimize=True)
    return output.getvalue()


def banner_filename(user_id: int) -> str:
    return f"welcome-{user_id}.png"
