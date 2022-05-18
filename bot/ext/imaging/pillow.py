from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from bot.utils.imaging.image import ImageConverter

if TYPE_CHECKING:
    from bot.bot import BombBot
    from bot.utils.context import BombContext

class Pillow(commands.Cog):

    def __init__(self, bot: BombBot) -> None:
        self.bot = bot

    @commands.command(name='imginfo', aliases=('img-info', 'image-info'))
    async def image_info(self, ctx: BombContext, *, image: str = None) -> None:
        """Sends image information and data of the provided image"""
        
        image = await ImageConverter().get_image(ctx, image)
        return await ctx.send(file=discord.File(image, 'test.png'))

async def setup(bot: BombBot) -> None:
    await bot.add_cog(Pillow(bot))