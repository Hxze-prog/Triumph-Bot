from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
FONT_DIR = ASSETS_DIR / "fonts"

_REGULAR_FILES = ("DejaVuSans.ttf",)
_BOLD_FILES = ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf")

_LINUX_DIRS = (Path("/usr/share/fonts"), Path("/usr/local/share/fonts"))
_WINDOWS_DIR = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
_WINDOWS_REGULAR = ("segoeui.ttf", "arial.ttf")
_WINDOWS_BOLD = ("seguisb.ttf", "segoeuib.ttf", "arialbd.ttf")


def _bundled(bold: bool) -> list[Path]:
    names = _BOLD_FILES if bold else _REGULAR_FILES
    return [FONT_DIR / name for name in names]


@lru_cache(maxsize=8)
def _linux_fonts(bold: bool) -> tuple[str, ...]:
    names = _BOLD_FILES if bold else _REGULAR_FILES
    found: list[str] = []
    for base in _LINUX_DIRS:
        if not base.exists():
            continue
        for name in names:
            for path in base.rglob(name):
                found.append(str(path))
                break
            if found:
                break
        if found:
            break
    return tuple(found)


def _candidates(bold: bool) -> list[str]:
    paths = [str(p) for p in _bundled(bold)]
    win_names = _WINDOWS_BOLD if bold else _WINDOWS_REGULAR
    paths.extend(str(_WINDOWS_DIR / name) for name in win_names)
    paths.extend(_linux_fonts(bold))
    return paths


@lru_cache(maxsize=64)
def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a TrueType font, preferring fonts bundled in bot/assets/fonts."""
    for candidate in _candidates(bold):
        path = Path(candidate)
        if not path.is_file():
            continue
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            continue
    raise RuntimeError(
        "No usable TrueType font found. Expected bot/assets/fonts/DejaVuSans.ttf "
        "or a system font (Windows segoeui/arial, Linux DejaVu)."
    )


def fonts_available() -> bool:
    try:
        load_font(24)
    except RuntimeError:
        return False
    return True
