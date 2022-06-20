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
    async def _boxplot(self, ctx: BombContext, *numbers: float) -> None:
        """Plots the providednumber data set in a box & whisker plot
        showing Min, Max, Mean, Q1, Median and Q3.
        Numbers should be seperated by spaces per data point.
        """
        return await do_command(ctx, numbers, func=boxplot)

    @commands.command(name='plot', aliases=('line-graph', 'graph'))
    async def _plot(self, ctx: BombContext, *, equation: str) -> None:
        """Plots the provided equation out.
        Ex: `{prefix}plot 2x+1`
        """
        try:
            return await do_command(ctx, equation, func=plotfn)
        except TypeError:
            await ctx.send(f'Provided equation was invalid; the only variable present must be `x`.')

async def setup(bot: BombBot) -> None:
    await bot.add_cog(Graphing(bot))