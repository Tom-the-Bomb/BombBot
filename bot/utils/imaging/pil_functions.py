from __future__ import annotations
from io import BytesIO

from typing import TYPE_CHECKING
import textwrap
import pathlib

import humanize
import discord
import numpy as np
from PIL import (
    Image,
    ImageOps,
    ImageFilter,
    ImageFont, 
    ImageDraw,
)

from ..helpers import to_thread, chunk, get_asset
from .image import (
    resize_pil_prop, 
    pil_colorize, 
    pil_image, 
    save_pil_image,
)

if TYPE_CHECKING:
    from ..context import BombContext

__all__: tuple[str, ...] = (
    'flip',
    'mirror',
    'contour',
    'lego',
    'minecraft',
    'type_gif',
    'image_info',
)

def _load_mc_colors() -> dict[tuple[int, int, int], Image.Image]:
    colors = {}
    for file in pathlib.Path(get_asset('minecraft/')).glob('*.png'):
        block = Image.open(get_asset(file)).convert('RGB')
        single = block.resize((1, 1))
        colors[single.getpixel((0, 0))] = block.resize((16, 16))
    return colors

# global image "cache"
UNICODE_FONT: ImageFont.FreeTypeFont = ImageFont.truetype(
    font=get_asset('GnuUnifontFull-Pm9P.ttf'), 
    size=25,
)
CODE_FONT: ImageFont.FreeTypeFont = ImageFont.truetype(
    font=get_asset('Monaco-Linux.ttf'), 
    size=18,
)
LEGO: Image.Image = (
    Image.open(
        get_asset('lego.png')
    )
    .convert('RGB')
    .resize((30, 30), Image.ANTIALIAS)
)
PAINT_MASK: Image.Image = (
    Image.open(
        get_asset('paint_mask.png')
    )
    .convert('L')
    .resize((20, 20), Image.ANTIALIAS)
)

MC_COLORS = _load_mc_colors()
MC_SAMPLE: np.ndarray = np.array(
    list(MC_COLORS.keys())
)

def _render_palette_image(colors: list[tuple[int, ...]]) -> Image.Image:
    CIRC, SPACE = 20, 5
    TOTALSP = CIRC + SPACE
    color_names = [f'rgb{tuple(c)}' for c in colors]
    width, _ = CODE_FONT.getsize_multiline(max(color_names, key=len))
    width += TOTALSP
    height = TOTALSP * 5

    y = 0
    base = Image.new('RGBA', (width, height), 0)
    cursor = ImageDraw.Draw(base)
    for color, color_name in zip(colors, color_names):
        with Image.new('RGB', (CIRC, CIRC), tuple(color)) as color_img:
            base.paste(color_img, (0, y), PAINT_MASK)
        cursor.text((TOTALSP, y - 3), color_name, font=CODE_FONT)
        y += TOTALSP
    return base

@pil_image()
def flip(_, img: Image.Image) -> Image.Image:
    return ImageOps.flip(img)

@pil_image()
def mirror(_, img: Image.Image) -> Image.Image:
    return ImageOps.mirror(img)

@pil_image()
def contour(_, img: Image.Image) -> Image.Image:
    return img.filter(ImageFilter.CONTOUR)

@pil_image(process_all_frames=False)
def lego(_, img: Image.Image, size: int = 50) -> Image.Image:
    img = resize_pil_prop(img, height=size, process_gif=False)
    with Image.new('RGBA', (img.width * LEGO.width, img.height * LEGO.height), 0) as bg:
        x, y = 0, 0
        for row in np.asarray(img.convert('RGBA')):
            for px in row:
                if px[-1] != 0:
                    piece = pil_colorize(LEGO, px)
                    bg.paste(piece, (x, y))
                x += LEGO.width
            x = 0
            y += LEGO.height
        return bg

@pil_image(process_all_frames=False)
def minecraft(_, img: Image.Image, size: int = 70) -> Image.Image:
    N = 16
    img = resize_pil_prop(img, height=size)
    bg = Image.new('RGBA', (img.width * N, img.height * N), 0)
    x, y = 0, 0
    for row in np.asarray(img.convert('RGBA')):
        for px in row:
            if px[-1] != 0:
                distances = np.sqrt(np.sum((MC_SAMPLE - px[:-1]) ** 2, axis=1))
                idx = np.where(distances == np.amin(distances))
                file = MC_COLORS[tuple(MC_SAMPLE[idx][0])]
                bg.paste(file, (x, y))
            x += N
        x = 0
        y += N
    return bg

@to_thread
def type_gif(_, text: str, *, duration: int = 50) -> discord.File:
    text = '\n'.join(textwrap.wrap(text, width=25, replace_whitespace=False))
    x, y = UNICODE_FONT.getsize_multiline(text)

    frames = []
    with Image.new('RGBA', (x + 10, y + 10), 0) as base:
        for i in range(len(text) + 1):
            img = base.copy()
            draw = ImageDraw.Draw(img)
            draw.multiline_text((3, 3), text[:i], fill=(245, 245, 220), font=UNICODE_FONT)
            frames.append(img)
    
    return save_pil_image(frames, duration=duration)

@pil_image(process_all_frames=False, auto_save=False, pass_buf=True)
def image_info(ctx: BombContext, source: BytesIO) -> tuple[discord.Embed, discord.File, discord.File] | tuple[discord.Embed, discord.File]:
    raw_bytes = source.getvalue()

    with Image.open(source) as img:
        embed = discord.Embed(
            color=ctx.bot.EMBED_COLOR,
            description=(
                f'```yml\nis-animated: {("no", "yes")[getattr(img, "is_animated", False)]}\n'
                f'Size: {img.width}x{img.height}\n'
                f'Mode: {img.mode or "N/A"}\n'
                f'Format: {img.format or "N/A"}\n'
                f'Size: {humanize.naturalsize(raw_bytes.__sizeof__())}\n'
                f'Frames: {getattr(img, "n_frames", 1)}\n'
            )
        )

        for key, value in img.info.items():
            key: str
            try:
                if isinstance(value, (list, tuple)):
                    value = ', '.join(map(
                        lambda f: f.decode(errors='ignore') if isinstance(f, bytes) else str(f), value
                    ))
                if isinstance(value, bytes):
                    value = value.decode(errors='ignore')
                embed.description += f'{key.title().replace("_", "-")}: {value}\n'
            except Exception:
                continue
        embed.description += '\n```'

        if palette := img.quantize(colors=5, method=Image.Quantize.FASTOCTREE).getpalette():
            palette = chunk(palette, count=3)[:5]
            palette_img = _render_palette_image(palette)
            palette_img = save_pil_image(palette_img)
            embed.set_image(url=f'attachment://{palette_img.filename}')

        thumbnail = discord.File(BytesIO(raw_bytes), f'image.{("png", "gif")[getattr(img, "is_animated", False)]}')
        embed.set_thumbnail(url=f'attachment://{thumbnail.filename}')

    try:
        return embed, thumbnail, palette_img
    except (NameError, UnboundLocalError):
        return embed, thumbnail