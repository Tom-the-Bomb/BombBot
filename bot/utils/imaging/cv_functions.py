from __future__ import annotations

from typing import TYPE_CHECKING, Final

import cv2
import numpy as np
from PIL import Image

from ..helpers import get_asset
from .image import (
    resize_cv_prop,
    get_closest_color,
    pil_image,
    to_array,
)

if TYPE_CHECKING:
    from wand.color import Color

__all__: tuple[str, ...] = (
    'lego',
    'lego_speed',
    'invert_scan',
    'cv_floor',
    'cartoon',
    'colordetect',
    'cornerdetect',
    'dilate',
    'canny',
)

BW: Final[np.ndarray] = np.array([[255, 255, 255], [0, 0, 0]])

LEGO: np.ndarray = cv2.imread(get_asset('lego.png'))
LEGO = cv2.resize(LEGO, (30, 30), interpolation=cv2.INTER_LANCZOS4)

def _gen_invert_frame(
    img: np.ndarray,
    span: int,
    bar_size: int,
    fuzz_span: float,
    *,
    spread: bool = True,
) -> np.ndarray:
    width = img.shape[1]
    img[:,:span] = ~img[:,:span]

    if spread:
        start = 0 if span <= bar_size else span - bar_size
        end = width if span >= width - bar_size else span + bar_size

        img[:,start:end] = np.asarray(
            Image.fromarray(img[:,start:end])
            .effect_spread(round(bar_size * fuzz_span))
        )
    return img

def _colorize_lego_band(band: np.ndarray, color: int) -> np.ndarray:
    band = band.astype(np.float32)
    new = color - 133 + band
    new[band < 33] = color - 100
    new[band > 233] = color + 100
    new[new < 0] = 0
    new[new > 255] = 255
    return new.astype(np.uint8)

def _colorize_lego(img: np.ndarray, color: tuple[int, int, int, int]) -> np.ndarray:
    red, green, blue = cv2.split(img)
    return cv2.merge((
        _colorize_lego_band(red, color[0]),
        _colorize_lego_band(green, color[1]),
        _colorize_lego_band(blue, color[2]),
        np.full((30, 30), color[3], dtype=np.uint8),
    ))

@pil_image()
@to_array('RGBA', cv2.COLOR_RGBA2BGRA)
def lego(_, img: np.ndarray, *, size: int = 40) -> np.ndarray:
    img = resize_cv_prop(img,
        height=size,
        resampling=cv2.INTER_AREA,
    )
    h, w, *_ = img.shape

    base = np.zeros((h * 30, w * 30, 4), dtype=np.uint8)
    x, y = 0, 0
    for row in img:
        for px in row:
            if px[-1] != 0:
                base[y:y + 30, x:x + 30] = _colorize_lego(LEGO, px)
            x += 30
        x = 0
        y += 30
    return base

@pil_image()
@to_array()
def lego_speed(_, img: np.ndarray, *, size: int = 40) -> np.ndarray:
    img = resize_cv_prop(img,
        height=size,
        resampling=cv2.INTER_AREA,
    )
    h, w, *_ = img.shape
    img = cv2.resize(img, (w * 30, h * 30), interpolation=cv2.INTER_NEAREST)

    base = np.tile(LEGO, [h, w, 1])
    blended = cv2.addWeighted(img, 0.7, base, 0.6, 0)
    return blended

@pil_image(width=400, process_all_frames=False)
@to_array('RGBA', cv2.COLOR_RGBA2BGRA)
def invert_scan(_, img: np.ndarray, *, spread: bool = True, bar_span: int = 12, fuzz_span: float = 0.8) -> list[np.ndarray]:
    width = img.shape[1]
    *rgb, a = cv2.split(img)
    img = cv2.merge(rgb)
    bar_size = width // bar_span

    frames = [
        _gen_invert_frame(img.copy(), i, bar_size, fuzz_span, spread=spread)
        for i in range(0, width, 10)
    ]
    frames += [~f for f in frames]
    frames = [cv2.merge(cv2.split(f) + (a,)) for f in frames]
    return frames

@pil_image(width=600)
@to_array('RGBA', cv2.COLOR_RGBA2BGRA)
def cv_floor(_, img: np.ndarray) -> np.ndarray:
    w, h, _ = img.shape

    _from = np.float32([
        [0, 0], [w, 0],
        [0, h], [w, h],
    ])
    _to = np.float32([
        [w * 0.3, h * 0.5],
        [w * 0.8, h * 0.5],
        [w * 0.1, h],
        [w * 0.9, h],
    ])
    transform = cv2.getPerspectiveTransform(_from, _to)
    img = cv2.warpPerspective(img, transform, (w, h), borderMode=cv2.BORDER_WRAP)
    return img

@pil_image()
@to_array()
def cartoon(_, img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
    color = cv2.bilateralFilter(img, 9, 250, 250)
    cartoon = cv2.bitwise_and(color, color, mask=edges)
    return cartoon

@pil_image()
@to_array('RGBA', cv2.COLOR_RGBA2BGRA)
def colordetect(_, img: np.ndarray, *, color: Color, fuzz: int = 15) -> np.ndarray:
    color = [int(val * 255) for val in (color.red, color.green, color.blue)]
    hsv_color = cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_RGB2HSV)
    hue_value = hsv_color[0, 0, 0]
    upper_hsv = np.array([hue_value + fuzz, 255, 255])
    lower_hsv = np.array([hue_value - fuzz, 100, 100])

    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_img, lower_hsv, upper_hsv)
    output = cv2.bitwise_and(img, img, mask=mask)
    return output

@pil_image(width=400)
@to_array('RGBA', cv2.COLOR_RGBA2BGRA)
def cornerdetect(_, img: np.ndarray, *, dot_size: int = 3):
    most_common = cv2.resize(img, (1, 1))[0, 0,:-1]
    color = [
        int(val) for val in get_closest_color(most_common, BW, reverse=True)
    ] + [255]

    gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    corners = cv2.goodFeaturesToTrack(gray, 100, 0.01, 10)
    corners = np.int0(corners)

    for corner in corners:
        x, y = corner.ravel()
        cv2.circle(img, (x, y), dot_size, color, -1)
    return img

@pil_image()
@to_array('RGBA', cv2.COLOR_RGBA2BGRA)
def dilate(_, img: np.ndarray) -> list[np.ndarray]:
    frames = [cv2.dilate(img, np.ones((i, i), np.uint8)) for i in range(1, 50, 2)]
    frames += reversed(frames)
    return frames

@pil_image()
@to_array('RGBA', cv2.COLOR_RGBA2BGRA)
def canny(_, img: np.ndarray) -> np.ndarray:
    return cv2.Canny(img, 100, 200)