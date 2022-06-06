from __future__ import annotations
from concurrent.futures import process
from io import BytesIO

from typing import TYPE_CHECKING, Any
import textwrap
import pathlib
import random
import string

import humanize
import discord
import numpy as np
import pilmoji
from PIL import (
    Image,
    ImageOps,
    ImageFilter,
    ImageDraw,
)

from ..helpers import to_thread, chunk, get_asset
from .fonts import *
from .image import (
    resize_pil_prop,
    get_closest_color,
    pil_colorize, 
    pil_image,
    pil_circle_mask,
    pil_circular,
    save_pil_image,
)

if TYPE_CHECKING:
    from ..context import BombContext

__all__: tuple[str, ...] = (
    'matrix',
    'flip',
    'mirror',
    'contour',
    'spin',
    'lego',
    'minecraft',
    'type_gif',
    'lines',
    'balls',
    'squares',
    'letters',
    'image_info',
    'caption',
    'bounce',
)

def _load_mc_colors() -> dict[tuple[int, int, int], Image.Image]:
    colors = {}
    for file in pathlib.Path(get_asset('minecraft/')).glob('*.png'):
        block = Image.open(get_asset(file)).convert('RGB')
        single = block.resize((1, 1))
        colors[single.getpixel((0, 0))] = block.resize((16, 16))
    return colors

# global image "cache"
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
PIL_CIRCLE_MASK: Image.Image = pil_circle_mask(1000, 1000)

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

def _gen_shape_frame(
    img: Image.Image, 
    method: str, 
    *, 
    size: int = 10, 
    count: int = 10000,
    **options: Any,
) -> Image.Image:

    text_arg = options.get('text')
    base = Image.new('RGBA', img.size, 0)
    cursor = ImageDraw.Draw(base)

    for _ in range(count):
        if text_arg:
            options['text'] = text_arg()
        x = random.randrange(1, img.width)
        y = random.randrange(1, img.height)

        _method = getattr(cursor, method, lambda *_: _)
        _method(
            xy=(x - size, y - size, x + size, y + size),
            fill=img.getpixel((x, y)),
            **options,
        )
    return base

def _generate_matrix_frame(img: Image.Image, *, size: int = 30) -> Image.Image:
    if CODE_FONT.size != size:
        font = CODE_FONT.font_variant(size=size)
    else:
        font = CODE_FONT

    base = Image.new('RGB', (img.width * size, img.height * size), 0)
    cursor = ImageDraw.Draw(base)
    x, y = 0, 0
    for row in np.asarray(img.convert('RGBA')):
        for px in row:
            if px[-1] != 0:
                cursor.text((x, y), random.choice(string.printable), font=font, fill=tuple(px[:-1]))
            x += size
        x = 0
        y += size
    return base

@pil_image(process_all_frames=False)
def matrix(_, img: Image.Image, *, size: int = 70) -> list[Image.Image]:
    img = resize_pil_prop(img, height=size, process_gif=False)
    return [_generate_matrix_frame(img) for _ in range(4)]

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
def spin(_, img: Image.Image) -> list[Image.Image]:
    img = img.convert('RGBA')
    img = pil_circular(img, mask=PIL_CIRCLE_MASK)

    frames = []
    for i in range(0, 360, 8):
        img = img.rotate(i, resample=Image.BICUBIC)
        frames.append(img)
        
    frames += reversed(frames)
    return frames

@pil_image(process_all_frames=False)
def lego(_, img: Image.Image, size: int = 50) -> Image.Image:
    img = resize_pil_prop(img, height=size, resampling=Image.BILINEAR, process_gif=False)
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
    img = resize_pil_prop(img, height=size, resampling=Image.BILINEAR, process_gif=False)
    bg = Image.new('RGBA', (img.width * N, img.height * N), 0)
    x, y = 0, 0
    for row in np.asarray(img.convert('RGBA')):
        for px in row:
            if px[-1] != 0:
                color = get_closest_color(px[:-1], MC_SAMPLE)
                file = MC_COLORS[color]
                bg.paste(file, (x, y))
            x += N
        x = 0
        y += N
    return bg

@to_thread
def type_gif(_, text: str, *, duration: int = 500) -> discord.File:
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

@pil_image(width=300, process_all_frames=False)
def lines(_, img: Image.Image) -> list[Image.Image]:
    img = img.convert('RGBA')
    return [_gen_shape_frame(img, 'line') for _ in range(3)]

@pil_image(width=300, process_all_frames=False)
def balls(_, img: Image.Image) -> list[Image.Image]:
    img = img.convert('RGBA')
    return [_gen_shape_frame(img, 'ellipse', outline='black') for _ in range(3)]

@pil_image(width=300, process_all_frames=False)
def squares(_, img: Image.Image) -> list[Image.Image]:
    img = img.convert('RGBA')
    return [_gen_shape_frame(img, 'rectangle') for _ in range(3)]

@pil_image(width=300, process_all_frames=False)
def letters(_, img: Image.Image) -> list[Image.Image]:
    img = img.convert('RGBA')
    return [
        _gen_shape_frame(
            img=img, 
            method='text', 
            text=lambda: random.choice(string.ascii_lowercase), 
            count=3000, 
            font=CODE_FONT, 
            anchor='mm',
        ) for _ in range(3)
    ]

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

@pil_image(width=300)
def caption(_, img: Image.Image, *, text: str) -> Image.Image:
    y, margin, spacing = 10, 10, 4
    fallback = UNICODE_FONT.font_variant(
        size=round(CAPTION_FONT.size * 0.8)
    )

    parts = textwrap.wrap(
        text=text, 
        width=15, 
        replace_whitespace=False,
    )
    text = '\n'.join(parts)

    text_width, extra_h = pilmoji.getsize(text, font=CAPTION_FONT)
    extra_h += margin * 2

    spacing = pilmoji.getsize('A', font=CAPTION_FONT)[1] + spacing
    
    if (max_width := text_width + margin * 2) >= img.width:
        img = resize_pil_prop(img, width=max_width)

    canvas = Image.new('RGBA', (img.width, img.height + extra_h), 'white')
    with pilmoji.Pilmoji(canvas) as draw:
        for line in parts:
            line_width = pilmoji.getsize(line, font=CAPTION_FONT)[0]
            x = start = img.width // 2 - line_width // 2

            for part, font in font_fallback(line, CAPTION_FONT, fallback):
                top = y
                if font == fallback:
                    top = top + 7
                draw.text((x, top), part, font=font, fill='black')
                x += pilmoji.getsize(part, font)[0]
            x = start
            y += spacing

    canvas.paste(img, (0, extra_h))
    return canvas

@pil_image(width=300, duration=60, process_all_frames=False)
def bounce(_, img: Image.Image, *, circular: bool = True) -> list[Image.Image]:
    img = img.convert('RGBA')

    if circular:
        img = pil_circular(img, mask=PIL_CIRCLE_MASK)

    frames = []
    for i in np.arange(-1, 1, 0.09):
        base = Image.new('RGBA', (img.width, img.height * 2), 0)
        translate = i ** 2
        base.paste(img, (0, round(img.height * translate)))
        frames.append(base)
    return frames