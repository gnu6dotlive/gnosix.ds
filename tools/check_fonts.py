"""Inspect native font glyph coverage before assigning a platform status."""

from pathlib import Path


def font_has_glyphs(path: Path, text: str) -> bool:
    from fontTools.ttLib import TTFont

    font = TTFont(path)
    try:
        cmap = font.getBestCmap() or {}
        return all(ord(char) in cmap for char in text)
    finally:
        font.close()
