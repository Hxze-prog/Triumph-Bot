from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw

from services import banner, fonts


def make_avatar(size: int = 256) -> bytes:
    image = Image.new("RGB", (size, size), (180, 60, 120))
    draw = ImageDraw.Draw(image)
    draw.ellipse((40, 40, size - 40, size - 40), fill=(250, 230, 120))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_fonts_available() -> None:
    assert fonts.fonts_available()
    assert fonts.load_font(24).size == 24
    assert fonts.load_font(24, bold=True).size == 24


def test_render_banner_produces_valid_png() -> None:
    png = banner.render_banner(
        display_name="Alice",
        subtitle="You are member #7",
        footer="Member #7 | Joined Nov 19, 2026",
        server_name="Triumph HQ",
        avatar_bytes=make_avatar(),
        accent=(88, 101, 242),
        initial="A",
    )
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    with Image.open(BytesIO(png)) as image:
        assert image.size == banner.BANNER_SIZE
        assert image.format == "PNG"


def test_render_banner_without_avatar() -> None:
    png = banner.render_banner(
        display_name="A very long display name " * 4,
        subtitle="",
        footer="",
        server_name="",
        avatar_bytes=None,
    )
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_accent_from_image() -> None:
    accent = banner.accent_from_image(make_avatar())
    assert len(accent) == 3
    assert all(0 <= channel <= 255 for channel in accent)


def test_accent_from_invalid_image_falls_back() -> None:
    assert banner.accent_from_image(b"not an image") == banner.DEFAULT_ACCENT
    assert banner.accent_from_image(None) == banner.DEFAULT_ACCENT


def test_banner_filename() -> None:
    assert banner.banner_filename(123) == "welcome-123.png"
