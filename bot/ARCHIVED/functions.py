
import numpy as np
from PIL import Image


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