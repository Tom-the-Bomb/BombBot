
import cv2
import numpy as np

from .image import pil_image, to_array

__all__: tuple[str, ...] = (
    'cartoon', 
    'canny',
)

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
@to_array()
def canny(_, img: np.ndarray) -> np.ndarray:
    return cv2.Canny(img, 100, 200)