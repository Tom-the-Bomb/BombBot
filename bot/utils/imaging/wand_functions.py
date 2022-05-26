from __future__ import annotations

from typing import TypeVar, TYPE_CHECKING

from wand.image import Image
from wand.sequence import SingleImage

from ..helpers import get_asset
from .image import (
    wand_circle_mask, 
    wand_image,
    wand_circular,
)

if TYPE_CHECKING:
    from wand.color import Color
    I = TypeVar('I', Image)

__all__: tuple[str, ...] = (
    'blur',
    'emboss',
    'invert',
    'colorize',
    'vignette',
    'wave',
    'polaroid',
    'fuzz',
    'sketch',
    'replace_color',
    'paint',
    'charcoal',
    'posterize',
    'solarize',
    'arc',
    'floor',
    'slide',
    'bulge',
    'swirl',
    'turn',
    'fisheye',
    'bomb',
    'cycle_colors',
    'huerotate',
    'spread_cards',
    'cube',
)

WAND_CIRCLE_MASK: Image = wand_circle_mask(1000, 1000)
WAND_SPHERE_OVERLAY: Image = Image(
    filename=get_asset('sphere.png')
)

@wand_image()
def blur(_, img: I, *, intensity: int = 3) -> I:
    img.gaussian_blur(sigma=intensity)
    return img

@wand_image()
def emboss(_, img: I) -> I:
    img.transform_colorspace('gray')
    img.shade(gray=True, azimuth=286.0, elevation=45.0)
    return img

@wand_image()
def invert(_, img: I, *, channel: str = 'RGB') -> I:
    img.negate(channel=channel)
    return img

@wand_image()
def colorize(_, img: I, *, color: Color) -> I:
    img.tint(color, 'rgb(60%, 60%, 60%)')
    return img

@wand_image()
def vignette(_, img: I, *, size: int = 10) -> I:
    img.vignette(sigma=3, x=size, y=size)
    return img

@wand_image()
def wave(_, img: I, *, count: int = 4) -> I:
    img.wave(amplitude=img.height / 24, wave_length=img.width / count)
    return img

@wand_image()
def polaroid(_, img: I) -> I:
    img.polaroid()
    return img

@wand_image()
def fuzz(_, img: I, *, intensity: int = 8) -> I:
    img.spread(radius=intensity)
    return img

@wand_image()
def replace_color(_, img: I, *, target: Color, to: Color) -> I:
    img.opaque_paint(target, to, fuzz=0.2 * img.quantum_range)
    return img

@wand_image()
def sketch(_, img: I) -> I:
    img.transform_colorspace('gray')
    img.sketch(0.5, 0.0, 98.0)
    return img

@wand_image()
def paint(_, img: I, *, spread: int = 3) -> I:
    img.oil_paint(radius=spread, sigma=3)
    return img

@wand_image()
def charcoal(_, img: I, *, intensity: float = 1.5) -> I:
    img.charcoal(radius=intensity, sigma=0)
    return img

@wand_image()
def posterize(_, img: I, *, static: bool = False, layers: int = 3) -> I:
    if static:
        img.posterize(layers)
        return img
    else:
        base = Image()
        for i in range(3, 13):
            with img.clone() as clone:
                clone.posterize(i)
                clone.delay = 10
                base.sequence.append(clone)
            del clone
        return base

@wand_image()
def solarize(_, img: I, *, threshold: float = 0.5, channel: str = 'RGB') -> I:
    img.solarize(
        threshold=threshold * img.quantum_range, 
        channel=channel,
    )
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
            img.width, img.height, img.width * 0.9, img.height,
        )
    )
    return img

@wand_image(width=300, process_all_frames=False)
def slide(_, img: Image) -> Image:
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
def bulge(_, img: Image) -> Image:
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
def swirl(_, img: Image) -> Image:
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

    if len(img.sequence) > 1 or img.format.lower() == 'gif':
        img = Image(img.sequence[0])
        img.dispose = 'background'

    img.rotate(12)
    for i in range(12, 360, 12):
        with img.clone() as clone:
            clone.rotate(i)
            clone.dispose = 'background'
            img.sequence.append(clone)
        del clone
    return img

@wand_image(width=400)
def fisheye(_, img: I, *, shade: bool = True, operator: str = 'screen') -> I:

    if isinstance(img, SingleImage):
        img = Image(img)

    img.background_color = 'none'
    img.virtual_pixel = 'background'
    img.distort('barrel', (1, 0, 0, 0.1))
    img.trim()
    wand_circular(img, mask=WAND_CIRCLE_MASK)
    
    if shade:
        with WAND_SPHERE_OVERLAY.clone() as overlay:
            overlay.resize(*img.size, filter='lanczos')
            img.composite(overlay, left=0, top=0, operator=operator)
        del overlay
    
    return img

@wand_image(width=400, process_all_frames=False)
def bomb(_, img: I) -> I:
    if len(img.sequence) == 1 or img.format.lower() != 'gif':
        img.sequence[0].delay = 200
        
    with Image(filename=get_asset('bomb.gif')) as bomb:
        if img.size != bomb.size:
            bomb.resize(*img.size, filter='lanczos')
        img.sequence.extend(bomb.sequence)
    return img

@wand_image(width=400, process_all_frames=False)
def cycle_colors(_, img: Image) -> Image:
    base = Image()
    for i in range(1, 360, 10):
        with img.clone() as frame:
            frame.cycle_color_map(i)
            frame.delay = 12
            frame.dispose = 'background'
            base.sequence.append(frame)
        del frame
    return base

@wand_image(width=400, process_all_frames=False)
def huerotate(_, img: Image) -> Image:
    base = Image()
    for i in range(1, 360, 10):
        with img.clone() as frame:
            frame.modulate(hue=i)
            frame.delay = 14
            frame.dispose = 'background'
            base.sequence.append(frame)
        del frame
    return base

@wand_image(process_all_frames=False)
def spread_cards(_, img: Image) -> Image:
    img.border('white', 10, 10)
    img.resize(300, 380, filter='lanczos')

    with img.clone() as clone:
        base = Image(width=500, height=480)
        base.sequence.append(img)

        for _ in range(9):
            clone = clone.clone()
            clone.rotate(10)
            base.sequence.append(clone)
    del clone
    return base

@wand_image(width=286, height=250)
def cube(_, img: Image) -> Image:
    img.alpha_channel = 'set'
    img.border('black', 2, 2)
    img.shear(background='transparent', x=-30)

    with img.clone() as top:
        top.rotate(-30, reset_coords=True)
        top.trim()
        base = Image(
            width=top.width, 
            height=top.height * 2,
            background='transparent'
        )
        base.composite(top, 0, 0)

    with img.clone() as left:
        left.rotate(30, reset_coords=True)
        left.trim()
        left.resize(left.width + 2, left.height)
        base.composite(left, 0, 144)

        left.flop()
        left.resize(left.width - 2, left.height)
        base.composite(left, base.width - left.width, 145)

    base.format = 'png'
    return base