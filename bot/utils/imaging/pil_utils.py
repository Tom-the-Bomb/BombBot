from __future__ import annotations

from typing import (
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
import asyncio

from PIL import Image

from .image import ImageConverter

if TYPE_CHECKING:
    from ..context import BombContext

    P = ParamSpec('P')
    C = TypeVar('C', BombContext)
    I = TypeVar('I', Image.Image)
    R = TypeVar('R', BytesIO)

    ImageParams: TypeAlias = Concatenate[C, I, P]
    ImageFunction: TypeAlias = Callable[ImageParams, R]
    Threaded: TypeAlias = Callable[ImageParams, Awaitable[R]]

__all__: tuple[str, ...] = (
    'resize_prop',
    'pil_image',
)

def resize_prop(img: Image.Image, width: Optional[int] = None, height: Optional[int] = None) -> Image.Image:

    if width and height:
        return img.resize((width, height))

    elif width:
        factor = img.width // width
        new_height = img.height // factor
        img = img.resize(width, new_height)

    elif height:
        factor = img.height // height
        new_height = img.width // factor
        img = img.resize(width, new_height)
    
    return img

def pil_image(width: Optional[int] = None, height: Optional[int] = None) -> Callable[[ImageFunction], Threaded]:
    def decorator(func: ImageFunction) -> Threaded:

        async def inner(ctx: C, img: I, *args: P.args, **kwargs: P.kwargs) -> R:
            img = await ImageConverter().get_image(ctx, img)

            image = Image.open(img)
            if width or height:
                image = resize_prop(image, width, height)
            return await asyncio.to_thread(func, ctx, image, *args, **kwargs)

        return inner
    return decorator