from __future__ import annotations

from typing import TYPE_CHECKING

from .image import wand_image

if TYPE_CHECKING:
    from wand.image import Image

__all__: tuple[str, ...] = (
    'invert',
    'arc',
)

@wand_image()
def invert(_, img: Image) -> Image:
    img.negate(channel='RGB')
    return img

@wand_image()
def arc(_, img: Image, degree: int) -> Image:
    img.background_color = 'transparent'
    img.virtual_pixel = 'background'
    img.distort(
        method='arc',
        arguments=(degree,),
    )
    return img