from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from bot.utils.imaging import do_command
from bot.utils.imaging.graphing import *

if TYPE_CHECKING:
    from bot.bot import BombBot
    from bot.utils.context import BombContext

class Graphing(commands.Cog):
    """Contains utility graphing / plotting commands
    powered by matplotlib and numpy
    """

    def __init__(self, bot: BombBot) -> None:
        self.bot = bot

    async def cog_unload(self) -> None:
        """Reloads the respective graphing modules on extension reload"""
        from importlib import reload
        from bot.utils.imaging import graphing

        reload(graphing)

    @commands.command(name='boxplot', aliases=('box', 'boxwhisker', 'numsetdata'))
    async def _boxplot(self, ctx: BombContext, dataset: commands.Greedy[float]) -> None:
        return await do_command(ctx, dataset, func=boxplot)

async def setup(bot: BombBot) -> None:
    await bot.add_cog(Graphing(bot))