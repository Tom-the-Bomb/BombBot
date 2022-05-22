from __future__ import annotations

from typing import TypeVar, TYPE_CHECKING

from wand.image import Image
from wand.sequence import SingleImage

from .image import (
    WAND_SPHERE_OVERLAY, 
    wand_image, 
    wand_circular,
)

if TYPE_CHECKING:
    I = TypeVar('I', Image)

__all__: tuple[str, ...] = (
    'invert',
    'arc',
    'floor',
    'slide',
    'bulge',
    'swirl',
    'turn',
    'sphere',
)

@wand_image()
def invert(_, img: I) -> I:
    img.negate(channel='RGB')
    return img

@wand_image(width=400)
def arc(_, img: I, degree: int = 180) -> I:
    img.background_color = 'transparent'
    img.virtual_pixel = 'background'
    img.distort(
        method='arc',
        arguments=(degree,),
    )
    return img

@wand_image(width=400)
def floor(_, img: I) -> I:
    img.virtual_pixel = 'tile'
    img.distort(
        method='perspective', 
        arguments=(
            0, 0, img.width * 0.3, img.height * 0.5,
            img.width, 0, img.width * 0.8, img.height * 0.5,
            0, img.height, img.width * 0.1, img.height,
            img.width, img.height, img.width * 0.9, img.height
        )
    )
    return img

@wand_image(width=300, process_all_frames=False)
def slide(_, img: I) -> I:
    base = Image(background='none')

    for i in range(2, 260, 20):
        with img.clone() as clone:
            clone.virtual_pixel = 'horizontal_tile'
            clone.distort('scale_rotate_translate', (i, 0, 1, 0, 0, 0))
            clone.distort('plane_2_cylinder', (110,))
            clone.dispose = 'background'
            base.sequence.append(clone)
        del clone
    return base

@wand_image(width=400, process_all_frames=False)
def bulge(_, img: I) -> I:
    base = Image(background='none')

    for i in range(0, -50, -5):
        with img.clone() as clone:
            clone.implode(amount=i)
            clone.dispose = 'background'
            base.sequence.append(clone)
        del clone
    
    for rframe in reversed(base.sequence):
        base.sequence.append(rframe)
        del rframe
    return base

@wand_image(width=400, process_all_frames=False)
def swirl(_, img: I) -> I:
    base = Image(background='none')

    for i in range(10, 140, 10):
        img = img.clone()
        img.swirl(degree=i)
        img.dispose = 'background'
        base.sequence.append(img)
    del img
    
    for rframe in reversed(base.sequence):
        base.sequence.append(rframe)
        del rframe
    return base

@wand_image(process_all_frames=False)
def turn(_, img: I) -> I:
    for i in range(0, 360, 12):
        with img.clone() as clone:
            clone.rotate(i)
            clone.background_color = 'none'
            clone.dispose = 'background'
            img.sequence.append(clone)
        del clone
    return img

@wand_image(width=300)
def sphere(_, img: I) -> I:

    if isinstance(img, SingleImage):
        img = Image(img)

    img.background_color = 'none'
    img.virtual_pixel = 'background'
    img.distort('barrel', (1, 0, 0, 0.2))
    img.trim()
    wand_circular(img)

    with WAND_SPHERE_OVERLAY.clone() as overlay:
        overlay.resize(*img.size, filter='lanczos')
        img.composite(overlay, left=0, top=0, operator='blend')
    del overlay
    
    return img