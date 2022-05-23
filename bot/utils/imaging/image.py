from __future__ import annotations

from typing import (
    Any,
    Final,
    Optional,
    Callable,
    TypeAlias,
    Concatenate,
    Awaitable,
    ParamSpec, 
    TypeVar, 
    TYPE_CHECKING,
)
from io import BytesIO
from math import ceil
import asyncio
import time

import numpy as np
import discord
from discord.ext import commands
from PIL import Image, ImageSequence
from wand.drawing import Drawing
from wand.image import Image as WandImage

from .converter import ImageConverter

if TYPE_CHECKING:
    from ..context import BombContext

    P = ParamSpec('P')
    C = TypeVar('C', BombContext)
    I = TypeVar('I', Image.Image)
    R = TypeVar('R', Image.Image, list[Image.Image], BytesIO)

    I_ = TypeVar('I_', WandImage)
    R_ = TypeVar('R_', WandImage, list[WandImage], BytesIO)

    CMD = TypeVar('CMD', bound=commands.Command)

    PillowParams: TypeAlias = Concatenate[C, I, P]
    PillowFunction: TypeAlias = Callable[PillowParams, R]
    PillowThreaded: TypeAlias = Callable[PillowParams, Awaitable[R]]

    WandParams: TypeAlias = Concatenate[C, I_, P]
    WandFunction: TypeAlias = Callable[WandParams, R_]
    WandThreaded: TypeAlias = Callable[WandParams, Awaitable[R_]]

    Duration: TypeAlias = list[int] | int | None

__all__: tuple[str, ...] = (
    'pil_colorize',
    'wand_circle_mask',
    'wand_circular',
    'resize_pil_prop',
    'resize_wand_prop',
    'process_wand_gif',
    'wand_save_list',
    'save_wand_image',
    'save_pil_image',
    'pil_image',
    'wand_image',
    'do_command',
)

FORMATS: Final[tuple[str, ...]] = ('png', 'gif')


def pil_colorize(img: Image.Image, color: tuple[int, int, int]) -> Image.Image:

    for i, (og, new) in enumerate(zip(bands := list(img.split()), color)):
        bands[i] = og.point(lambda c: new - 100 if c < 33 else new + 100 if c > 233 else new - 133 + c)

    return Image.merge(img.mode, bands)

def wand_circle_mask(width: int, height: int) -> I_:
    mask = WandImage(
        width=width, height=height, 
        background='transparent', colorspace='gray'
    )
    mask.antialias = True
    with Drawing() as draw:
        draw.stroke_color = 'black'
        draw.stroke_width = 1
        draw.fill_color = 'white'
        draw.circle(
            (width // 2, height // 2), 
            (width // 2, 0)
        )
        draw(mask)
    return mask

def wand_circular(img: I_, *, mask: Optional[WandImage] = None) -> I_:

    if mask.size != img.size:
        mask = mask.clone()
        mask.resize(*img.size, filter='lanczos')

    img.composite(mask, left=0, top=0, operator='copy_alpha')
    return img


def _get_prop_size(
    image: Image.Image | WandImage,
    width: Optional[int] = None, 
    height: Optional[int] = None,
) -> tuple[int, int]:

    if width:
        height = ceil((width / image.width) * image.height)
    elif height:
        width = ceil((height / image.height) * image.width)
    else:
        width, height = image.size

    return width, height


def process_wand_gif(
    image: I_, 
    func: WandFunction, 
    ctx: BombContext,
    *args: P.args, 
    **kwargs: P.kwargs,
) -> I_:

    for i, frame in enumerate(image.sequence):
        result = func(ctx, frame, *args, **kwargs)
        result.dispose = 'background'
        image.sequence[i] = result

    image.dispose = 'background'
    image.format = 'GIF'
    return image

def resize_pil_prop(
    image: Image.Image, 
    width: Optional[int] = None, 
    height: Optional[int] = None, 
    *,
    resampling: Image.Resampling = Image.ANTIALIAS,
) -> list[Image.Image] | Image.Image:

    if not (width and height):
        width, height = _get_prop_size(image, width, height)

    def resize_image(img: Image.Image) -> Image.Image:
        return img.resize((width, height), resampling)
    
    if getattr(image, 'is_animated', False):
        image = ImageSequence.all_frames(image, resize_image)
    else:
        return resize_image(image)

def resize_wand_prop(
    image: WandImage, 
    width: Optional[int] = None, 
    height: Optional[int] = None, 
    *,
    resampling: str = 'lanczos',
) -> WandImage:

    if not (width and height):
        width, height = _get_prop_size(image, width, height)

    image.resize(width, height, filter=resampling)
    return image


def wand_save_list(
    frames: list[Image.Image | WandImage] | ImageSequence.Iterator, 
    duration: Duration,
) -> WandImage:
    
    is_pil = (
        isinstance(frames, ImageSequence.Iterator) or
        isinstance(frames[0], Image.Image)
    )

    base = WandImage()

    for i, frame in enumerate(frames):

        if is_pil:
            frame = np.asarray(frame.convert('RGBA'))
            frame = WandImage.from_array(frame)
        
        frame.dispose = 'background'
        
        if isinstance(duration, list):
            frame.delay = duration[i]
        elif duration is not None:
            frame.delay = duration
        base.sequence.append(frame)

    base.dispose = 'background'
    base.format = 'GIF'
    return base


def save_wand_image(
    image: WandImage | list[Image.Image | WandImage] | ImageSequence.Iterator,
    *,
    duration: Duration = None,
    file: bool = True,
) -> discord.File | BytesIO:

    is_list = isinstance(image, (list, ImageSequence.Iterator))

    is_gif = (
        is_list or 
        getattr(image, 'format', '').lower() == 'gif' or 
        len(getattr(image, 'sequence', [])) > 1
    )

    if is_list:
        image = wand_save_list(image, duration)

    elif is_gif:
        image.format = 'GIF'
        image.dispose = 'background'

    output = BytesIO()
    image.save(file=output)
    output.seek(0)

    image.close()
    del image

    if file:
        output = discord.File(output, f'output.{FORMATS[is_gif]}')
    return output


def save_pil_image(
    image: Image.Image | list[Image.Image], 
    *, 
    duration: Optional[int] = None,
    file: bool = True,
) -> discord.File | BytesIO:

    if is_gif := isinstance(image, list):
        return save_wand_image(image, duration=duration)

    elif is_gif := getattr(image, 'is_animated', False):
        return save_wand_image(ImageSequence.Iterator(image), duration=duration)

    output = BytesIO()
    image.save(output, format='PNG')
    output.seek(0)

    image.close()
    del image

    if file:
        output = discord.File(output, f'output.{FORMATS[is_gif]}')
    return output


def pil_image(
    width: Optional[int] = None, 
    height: Optional[int] = None, 
    *,
    process_all_frames: bool = True,
    duration: Duration = None,
    auto_save: bool = True,
    to_file: bool = True,
) -> Callable[[PillowFunction], PillowThreaded]:
    def decorator(func: PillowFunction) -> PillowThreaded:

        async def wrapper(ctx: C, img: I, *args: P.args, **kwargs: P.kwargs) -> R:
            img = await ImageConverter().get_image(ctx, img)
            
            def inner(img: BytesIO) -> R:
                image = Image.open(img)
                if width or height:
                    image = resize_pil_prop(image, width, height)

                if process_all_frames and (getattr(image, 'is_animated', False) or image.format.lower() == 'gif'):
                    result = ImageSequence.all_frames(image, lambda frame: func(ctx, frame, *args, **kwargs))
                else:
                    result = func(ctx, image, *args, **kwargs)

                if auto_save and isinstance(result, (Image.Image, list, ImageSequence.Iterator)):
                    result = save_pil_image(result, duration=duration, file=to_file)
                return result

            return await asyncio.to_thread(inner, img)
        return wrapper
    return decorator


def wand_image(
    width: Optional[int] = None, 
    height: Optional[int] = None, 
    *,
    process_all_frames: bool = True,
    duration: Duration = None,
    auto_save: bool = True,
    to_file: bool = True,
) -> Callable[[WandFunction], WandThreaded]:
    def decorator(func: WandFunction) -> WandThreaded:

        async def wrapper(ctx: C, img: I, *args: P.args, **kwargs: P.kwargs) -> R_:
            img = await ImageConverter().get_image(ctx, img)

            def inner(img: BytesIO) -> R_:
                image = WandImage(file=img)
                image.background_color = 'none'

                if width or height:
                    image = resize_wand_prop(image, width, height)

                if process_all_frames and (len(image.sequence) > 1 or image.format.lower() == 'gif'):
                    result = process_wand_gif(image, func, ctx, *args, **kwargs)
                else:
                    result = func(ctx, image, *args, **kwargs)

                if auto_save and isinstance(result, (WandImage, list)):
                    result = save_wand_image(result, duration=duration, file=to_file)
                return result

            return await asyncio.to_thread(inner, img)
        return wrapper
    return decorator


async def _do_command_body(
    ctx: BombContext, 
    image: Optional[str],
    func: WandThreaded | PillowThreaded,
    **kwargs: Any,
) -> None:

    start = time.perf_counter()
    file = await func(ctx, image, **kwargs)
    end = time.perf_counter()
    elapsed = (end - start) * 1000

    await ctx.reply(
        content=f'**Process Time:** `{elapsed:.2f} ms`', 
        file=file,
        mention_author=False,
        delete_button=True,
    )

async def do_command(
    ctx: BombContext, 
    image: Optional[str],
    func: WandThreaded | PillowThreaded,
    *,
    load: bool = True,
    **kwargs: Any,
) -> None:
    if load:
        async with ctx.loading():
            return await _do_command_body(ctx, image, func=func, **kwargs)
    else:
        return await _do_command_body(ctx, image, func=func, **kwargs)