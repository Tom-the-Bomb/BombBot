
from typing import Optional

import discord
from discord.ext import commands

from ..bot import BombBot
from ..utils.image import ImageConverter
from ..utils.context import BombContext

class Image(commands.Cog):

    def __init__(self, bot: BombBot) -> None:
        self.bot = bot

    @commands.command(name='test')
    async def test(self, ctx: BombContext, *, image: str = None) -> None:
        image = await ImageConverter().get_image(ctx, image)
        return await ctx.send(file=discord.File(image, 'test.png'))

async def setup(bot: BombBot) -> None:
    await bot.add_cog(Image(bot))