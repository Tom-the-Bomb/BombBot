from __future__ import annotations

from typing import TYPE_CHECKING
import inspect

from discord.ext import commands

from bot.utils.imaging import wand_image, image_command

if TYPE_CHECKING:
    from wand.image import Image

    from bot.bot import BombBot
    from bot.utils.context import BombContext

class WandFunctions:

    @image_command(name='invert')
    @wand_image()
    def invert(ctx: BombContext, image: Image) -> None:
        """Inverts the provided `image`'s provided"""

        image.negate(channel='RGB')
        return image

class Wand(commands.Cog):
    """Cog containing image manipulation commands utilizing `wand`
    """
    def __init__(self, bot: BombBot) -> None:
        self.bot = bot

        for _, func in inspect.getmembers(WandFunctions()):
            print(func)
            if isinstance(func, commands.Command):
                bot.add_command(func)
                func.cog = self

async def setup(bot: BombBot) -> None:
    await bot.add_cog(Wand(bot))