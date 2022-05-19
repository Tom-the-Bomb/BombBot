from __future__ import annotations

from typing import (
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
from enum import Enum
import asyncio

import discord
import numpy as np
from PIL import Image, ImageSequence
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

    PillowParams: TypeAlias = Concatenate[C, I, P]
    PillowFunction: TypeAlias = Callable[PillowParams, R]
    PillowThreaded: TypeAlias = Callable[PillowParams, Awaitable[R]]

    WandParams: TypeAlias = Concatenate[C, I_, P]
    WandFunction: TypeAlias = Callable[WandParams, R_]
    WandThreaded: TypeAlias = Callable[WandParams, Awaitable[R_]]

__all__: tuple[str, ...] = (
    'resize_prop',
    'pil_image',
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


def resize_pil_prop(
    image: Image.Image, 
    width: Optional[int] = None, 
    height: Optional[int] = None, 
    *,
    resampling: Image.Resampling = Image.ANTIALIAS,
) -> Image.Image:

    if not (width and height):
        width, height = _get_prop_size(image, width, height)
    return image.resize((width, height), resampling)


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
    duration: int | list[int],
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
    duration: int | list[int] = None,
    *,
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
                result = func(ctx, image, *args, **kwargs)

                if auto_save:
                    result = save_pil_image(result, file=to_file)
                return result

            return await asyncio.to_thread(inner, img)
        return wrapper
    return decorator


def wand_image(
    width: Optional[int] = None, 
    height: Optional[int] = None, 
    *, 
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
                result = func(ctx, image, *args, **kwargs)

                if auto_save:
                    result = save_wand_image(result, file=to_file)
                return result

            return await asyncio.to_thread(inner, img)
        return wrapper
    return decorator