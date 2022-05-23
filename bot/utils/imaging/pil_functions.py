from __future__ import annotations

from typing import Sequence, TYPE_CHECKING
import textwrap

import humanize
import discord
from PIL import (
    Image, 
    ImageFont, 
    ImageDraw,
)

from ..helpers import to_thread, chunk
from .image import pil_image, save_pil_image

if TYPE_CHECKING:
    from ..context import BombContext

__all__: tuple[str, ...] = (
    'type_gif',
    'image_info',
)

CODE_FONT: ImageFont.FreeTypeFont = ImageFont.truetype('C:/Users/Tom the Bomb/BombBot/assets/GnuUnifontFull-Pm9P.ttf', 25)

@to_thread
def type_gif(_, text: str, *, duration: int = 50) -> list[Image.Image]:
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