from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Literal, ClassVar
import unicodedata

import discord
from discord.ext import commands
from jishaku.codeblocks import codeblock_converter

from async_tio import Tio

from ..utils.calculator import CalculatorView

if TYPE_CHECKING:
    from ..bot import BombBot
    from ..utils.context import BombContext

class Utility(commands.Cog):
    """Contains various useful utility commands"""
    CHARINFO_URL: ClassVar[str] = 'https://www.fileformat.info/info/unicode'

    def __init__(self, bot: BombBot) -> None:
        self.bot = bot
        self.tio = Tio(session=bot.session)

    async def cog_unload(self) -> None:
        from importlib import reload
        from ..utils import calculator

        reload(calculator)

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

    @commands.command(name='charinfo', aliases=('char', 'chr'))
    async def charinfo(self, ctx: BombContext, *, chars: str) -> None:
        """Provides information on each **character** from the given argument and the raw unicode of the characters"""

        embed = discord.Embed(
            title='Unicode Character Info',
            color=ctx.bot.EMBED_COLOR,
            description='',
            url=self.CHARINFO_URL,
        )
        raw_text = ''
        for char in chars:
            digit = format(ord(char), 'x')
            raw_text += (
                u_code := f'\\u{digit:>04}' if len(digit) <= 4 else f'\\U{digit:>08}'
            )
            url = f'{self.CHARINFO_URL}/char/{digit:>04}/index.htm'
            name = f'**[{unicodedata.name(char, "")}]({url})**'

            embed.description += (
                f'`{u_code.ljust(10).replace(" ", "")}`'
                f' | {name}\t•\t**{discord.utils.escape_markdown(char)}**\n'
            )
        embed.description += '\n\u200b'
        embed.add_field(
            name='Full Raw Text',
            value=f'`{raw_text}`',
        )
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send('The character string is too long!')

    @commands.command(name='calculator', aliases=('calc',))
    async def calculator(self, ctx: BombContext) -> None:
        """A generic arithmetic calculator with a matrix of buttons"""
        await ctx.send(
            embed=discord.Embed(
                description=f'```py\n\u200b{" " * 40}\u200b\n```',
                color=ctx.bot.EMBED_COLOR,
            ),
            view=CalculatorView(ctx, timeout=900),
        )

async def setup(bot: BombBot) -> None:
    await bot.add_cog(Utility(bot))