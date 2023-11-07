
import re

import numpy as np
from PIL import Image

from ..utils.helpers import get_asset
from ..utils.imaging import pil_image, resize_pil_prop


# for old lego function
LEGO: Image.Image = (
    Image.open(
        get_asset('lego.png')
    )
    .convert('RGBA')
    .resize((30, 30), Image.ANTIALIAS)
)

def colorize_lego_band(band: np.ndarray, color: int) -> np.ndarray:
    """an alternative but slightly slower algorithm for colorizing lego bands"""
    band = band.astype(np.float32)
    arr = np.where(
        band < 33,
        color - 100,
        np.where(
            band > 233,
            color + 100,
            color - 133 + band,
        )
    )
    arr[arr < 0] = 0
    arr[arr > 255] = 255
    return arr.astype(np.uint8)

def _calc_colorize(color: int, new: int) -> int:
    if color < 33:
        return new - 100
    elif color > 233:
        return new + 100
    else:
        return new - 133 + color

def pil_colorize(img: Image.Image, color: tuple[int, int, int, int]) -> Image.Image:

    red, green, blue, alpha = img.split()
    red = red.point(
        lambda col: _calc_colorize(col, color[0])
    )
    green = green.point(
        lambda col: _calc_colorize(col, color[1])
    )
    blue = blue.point(
        lambda col: _calc_colorize(col, color[2])
    )
    alpha = alpha.point(
        lambda col: _calc_colorize(col, color[3])
    )

    return Image.merge(img.mode, (red, green, blue, alpha))

@pil_image(process_all_frames=False)
def lego(_, img: Image.Image, size: int = 40) -> Image.Image:
    """Old lego function using pil, was slow."""
    img = resize_pil_prop(img, height=size, resampling=Image.BILINEAR, process_gif=False)
    with Image.new('RGBA', (img.width * LEGO.width, img.height * LEGO.height), 0) as bg:
        x, y = 0, 0
        for row in np.asarray(img.convert('RGBA')):
            for px in row:
                if px[-1] != 0:
                    piece = pil_colorize(LEGO, px)
                    bg.paste(piece, (x, y))
                x += LEGO.width
            x = 0
            y += LEGO.height
        return bg

# for old graphing equation parsing
def _clean_implicit_mul(equation: str) -> str:
    def _sub_mul(val: re.Match) -> str:
        parts = list(val.group())
        parts.insert(-1, '*')
        return ''.join(parts)

    equation = re.sub(r'\s+', '', equation)
    equation = re.sub(r'(?<=[0-9x)])x', _sub_mul, equation)
    equation = equation.replace(')(', ')*(')
    return equation