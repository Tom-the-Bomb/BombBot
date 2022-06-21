from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Literal

import discord
from discord.ext import commands
from jishaku.codeblocks import codeblock_converter

from async_tio import Tio

if TYPE_CHECKING:
    from ..bot import BombBot
    from ..utils.context import BombContext

class Utility(commands.Cog):
    """Contains various useful utility commands"""

    def __init__(self, bot: BombBot) -> None:
        self.bot = bot
        self.tio = Tio(session=bot.session)

    @commands.command(name='execute', aliases=('eval', 'run'))
    async def execute(self, ctx: BombContext, language: str, *, code: codeblock_converter) -> None:
        """executes the provided `code` in the provided `language`"""

        response = await self.tio.execute(code.content, language=language)
        output = f'```{code.language or language or "yml"}\n{response.output}\n```'

        if len(output) > 2000:
            await ctx.send(await ctx.bot.post_mystbin(response.output))
        else:
            await ctx.send(output)

    @commands.command(name='latex', aliases=('tex',))
    async def latex(self, ctx: BombContext, light_mode: Optional[Literal['-l']], *, latex: codeblock_converter) -> None:
        """Renders the provided latex equation

        Specify the optional `-l` option if you are using discord light mode (white text)
        """

        file = await ctx.bot.render_latex(latex.content, light_mode=bool(light_mode))
        embed = discord.Embed(color=ctx.bot.EMBED_COLOR)
        embed.set_image(url=f'attachment://{file.filename}')
        await ctx.send(file=file, embed=embed)

async def setup(bot: BombBot) -> None:
    await bot.add_cog(Utility(bot))