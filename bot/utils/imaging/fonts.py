import re

from fontTools.ttLib import TTFont
from PIL import ImageFont

from ..helpers import get_asset

__all__: tuple[str, ...] = (
    'font_fallback',
    'UNICODE_FONT',
    'CODE_FONT',
    'CAPTION_FONT',
)


def _get_font_glyphs(font_path: str) -> list[str]:
    with TTFont(font_path) as font:
        return [
            chr(font.getGlyphID(name) + 29) for name in font.getGlyphOrder()
        ]

def font_fallback(
    text: str,
    font: ImageFont.FreeTypeFont,
    fallback: ImageFont.FreeTypeFont,
) -> list[tuple[str, ImageFont.FreeTypeFont]]:

    if not (glyphs := getattr(font, 'glyphs', None)):
        glyphs = _get_font_glyphs(font)

    glyphs = ''.join(map(re.escape, glyphs))
    parts = re.split(fr'([^{glyphs}]+)', text)
    return [
        (part, (fallback, font)[all(char in glyphs for char in part)])
        for part in parts
    ]

# font constants
UNICODE_FONT: ImageFont.FreeTypeFont = ImageFont.truetype(
    font=get_asset('GnuUnifontFull-Pm9P.ttf'),
    size=25,
)
UNICODE_FONT.glyphs = _get_font_glyphs(UNICODE_FONT.path)

CODE_FONT: ImageFont.FreeTypeFont = ImageFont.truetype(
    font=get_asset('Monaco-Linux.ttf'),
    size=18,
)
CODE_FONT.glyphs = _get_font_glyphs(CODE_FONT.path)

CAPTION_FONT: ImageFont.FreeTypeFont = ImageFont.truetype(
    font=get_asset('impact.ttf'),
    size=30,
)
CAPTION_FONT.glyphs = _get_font_glyphs(CAPTION_FONT.path)