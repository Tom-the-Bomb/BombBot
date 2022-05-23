from __future__ import annotations

from typing import Sequence, TYPE_CHECKING
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
from .image import pil_colorize, pil_image, save_pil_image

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

CODE_FONT: ImageFont.FreeTypeFont = ImageFont.truetype(get_asset('GnuUnifontFull-Pm9P.ttf'), 25)
LEGO: Image.Image = Image.open(get_asset('lego.png')).convert('RGB')

MC_COLORS = _load_mc_colors()
MC_SAMPLE: np.ndarray = np.array(list(MC_COLORS.keys()))

@pil_image()
def flip(_, img: Image.Image) -> Image.Image:
    return ImageOps.flip(img)

@pil_image()
def mirror(_, img: Image.Image) -> Image.Image:
    return ImageOps.mirror(img)

@pil_image()
def contour(_, img: Image.Image) -> Image.Image:
    return img.filter(ImageFilter.CONTOUR)

@pil_image(height=50, process_all_frames=False)
def lego(_, img: Image.Image) -> Image.Image:
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

@pil_image(height=70, process_all_frames=False)
def minecraft(_, img: Image.Image) -> Image.Image:
    N = 16
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
    x, y = CODE_FONT.getsize_multiline(text)

    frames = []
    with Image.new('RGBA', (x + 10, y + 10), 0) as base:
        for i in range(len(text) + 1):
            img = base.copy()
            draw = ImageDraw.Draw(img)
            draw.multiline_text((3, 3), text[:i], fill=(245, 245, 220), font=CODE_FONT)
            frames.append(img)
    
    return save_pil_image(frames, duration=duration)

@pil_image(process_all_frames=False, auto_save=False)
def image_info(ctx: BombContext, img: Image.Image) -> tuple[discord.File, discord.Embed]:
    byt = img.tobytes()
    embed = discord.Embed(
        color=ctx.bot.EMBED_COLOR,
        description=(
            f'```yml\nis-animated: {getattr(img, "is_animated", False)}\n'
            f'Size: {img.width}x{img.height}\n'
            f'Mode: {img.mode or "N/A"}\n'
            f'Format: {img.format or "N/A"}\n'
            f'Size: {humanize.naturalsize(byt.__sizeof__())}\n'
            f'Frames: {getattr(img, "n_frames", 1)}\n'
        )
    )

    for key, value in img.info.items():
        key: str
        try:
            if isinstance(value, Sequence):
                value = ', '.join(map(
                    lambda f: f.decode(errors='ignore') if isinstance(f, bytes) else str(f), value
                ))
            if isinstance(value, bytes):
                value = value.decode(errors='ignore')
            embed.description += f'{key.title().replace("_", "-")}: {value}\n'
        except Exception:
            continue

    if palette := img.convert('P').getpalette():
        palette = chunk(palette, count=3)[:5]
        palette = '  - ' + '\n  - '.join(map(lambda c: f'rgb{tuple(c)}', palette))
        embed.description += f'---\nTop-palette:\n{palette}'
    embed.description += '\n```'

    file = save_pil_image(img, duration=img.info.get('duration'))
    embed.set_thumbnail(url=f'attachment://{file.filename}')
    return file, embed