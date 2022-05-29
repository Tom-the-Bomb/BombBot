from __future__ import annotations

from typing import TYPE_CHECKING, Final

import cv2
import numpy as np

from .image import get_closest_color, pil_image, to_array

if TYPE_CHECKING:
    from wand.color import Color

__all__: tuple[str, ...] = (
    'cartoon',
    'colordetect',
    'cornerdetect',
    'dilate',
    'canny',
)

BW: Final[np.ndarray] = np.array([[255, 255, 255], [0, 0, 0]])


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