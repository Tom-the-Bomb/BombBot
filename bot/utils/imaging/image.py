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
from wand.image import Image as WandImage

from .converter import ImageConverter
from ..context import BombContext
if TYPE_CHECKING:

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
    'resize_pil_prop',
    'resize_wand_prop',
    'process_wand_gif',
    'wand_save_list',
    'save_wand_image',
    'save_pil_image',
    'pil_image',
    'wand_image',
    'image_command',
)

FORMATS: Final[tuple[str, ...]] = ('png', 'gif')


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
    image.format = 'gif'
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
    base.format = 'gif'
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
        getattr(image, 'format', None) == 'gif' or 
        len(getattr(image, 'sequence', [])) > 0
    )

    if is_list:
        image = wand_save_list(image, duration)

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
        return save_wand_image(image, duration)

    elif is_gif := getattr(image, 'is_animated', False):
        return save_wand_image(ImageSequence.Iterator(image), duration)

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

                if getattr(image, 'is_animated', False) or image.format == 'gif':
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
    duration: Duration = None,
    auto_save: bool = True,
    to_file: bool = True,
) -> Callable[[WandFunction], WandThreaded]:
    def decorator(func: WandFunction) -> WandThreaded:

        async def wrapper(ctx: C, img: I, *args: P.args, **kwargs: P.kwargs) -> R_:
            img = await ImageConverter().get_image(ctx, img)

            def inner(img: BytesIO) -> R_:
                image = WandImage(file=img)
                if width or height:
                    image = resize_wand_prop(image, width, height)

                if image.sequence or image.format == 'gif':
                    result = process_wand_gif(image, func, ctx, *args, **kwargs)
                else:
                    result = func(ctx, image, *args, **kwargs)

                if auto_save and isinstance(result, (WandImage, list)):
                    result = save_wand_image(result, duration=duration, file=to_file)
                return result

            return await asyncio.to_thread(inner, img)
        return wrapper
    return decorator


async def _do_command(
    ctx: BombContext, 
    image: Optional[str] = None, 
    *, 
    func: WandThreaded | PillowThreaded,
) -> None:

    start = time.perf_counter()
    file = await func(ctx, image)
    end = time.perf_counter()
    elapsed = (end - start) * 1000

    await ctx.send(
        content=f'**Process Time:** `{elapsed:.2f}`', 
        file=file,
    )


def image_command(*, load: bool = True, **kwargs: Any) -> Callable[[WandThreaded | PillowThreaded], CMD]:
    def decorator(func: WandThreaded | PillowThreaded) -> CMD:

        @commands.command(**kwargs)
        async def command_callback(ctx: BombContext, *, image: str = None) -> None:
            
            if load:
                async with ctx.loading():
                    return await _do_command(ctx, image, func=func)
            else:
                return await _do_command(ctx, image, func=func)
                
        return command_callback
    return decorator