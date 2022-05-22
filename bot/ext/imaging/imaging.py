from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from bot.utils.imaging import do_command
from bot.utils.imaging.pil_functions import *
from bot.utils.imaging.wand_functions import *

if TYPE_CHECKING:
    from bot.bot import BombBot
    from bot.utils.context import BombContext

class Imaging(commands.Cog):
    """Cog containing image manipulation commands utilizing `wand` & `pillow`
    """
    def __init__(self, bot: BombBot) -> None:
        self.bot = bot

    # wand functions
    @commands.command(name='invert')
    async def _invert(self, ctx: BombContext, *, image: str = None) -> None:
        return await do_command(ctx, image, func=invert)

    @commands.command(name='arc')
    async def _arc(self, ctx: BombContext, *, image: str = None) -> None:
        return await do_command(ctx, image, func=arc)

    @commands.command(name='floor')
    async def _floor(self, ctx: BombContext, *, image: str = None) -> None:
        return await do_command(ctx, image, func=floor)

    @commands.command(name='gallery')
    async def _gallery(self, ctx: BombContext, *, image: str = None) -> None:
        return await do_command(ctx, image, func=slide)

    @commands.command(name='bulge')
    async def _bulge(self, ctx: BombContext, *, image: str = None) -> None:
        return await do_command(ctx, image, func=bulge)

    @commands.command(name='swirl')
    async def _swirl(self, ctx: BombContext, *, image: str = None) -> None:
        return await do_command(ctx, image, func=swirl)

    @commands.command(name='turn')
    async def _turn(self, ctx: BombContext, *, image: str = None) -> None:
        return await do_command(ctx, image, func=turn)

    @commands.command(name='sphere')
    async def _sphere(self, ctx: BombContext, *, image: str = None) -> None:
        return await do_command(ctx, image, func=sphere)
    
    # pil functions

async def setup(bot: BombBot) -> None:
    from importlib import reload
    from bot.utils.imaging import pil_functions
    from bot.utils.imaging import wand_functions

    reload(pil_functions)
    reload(wand_functions)
    
    await bot.add_cog(Imaging(bot))