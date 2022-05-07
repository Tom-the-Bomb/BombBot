
from typing import Final
from io import BytesIO, StringIO
import contextlib

import discord
from discord.ext import commands

from PIL import Image
from jishaku.codeblocks import codeblock_converter
from fstop import Runner

from ..utils.context import BombContext
from ..bot import BombBot

class Owner(commands.Cog):

    def __init__(self, bot: BombBot) -> None:
        self.bot = BombBot
        self.runner: Final[Runner] = Runner(reset_after_execute=True)

    @commands.command(name='fstop', aliases=['fs'])
    @commands.is_owner()
    async def run_fstop(self, ctx: BombContext, *, code: codeblock_converter) -> discord.Message:

        stream = StringIO()
        with contextlib.redirect_stdout(stream):
            self.runner.execute(
                code.content, 
                streams=[
                    BytesIO(await ctx.author.avatar.read()),
                    BytesIO(await ctx.bot.user.avatar.read()),
                ]
            )
        try:
            output = self.runner.streams[0]
        except IndexError:
            content = stream.getvalue() or '\u200b'
            return await ctx.send(f'```py\n{content}\n```')
        else:
            with Image.open(BytesIO(output.getvalue())) as img:
                ext = img.format.lower()
            return await ctx.send(file=discord.File(output, f'output.{ext}'))

async def setup(bot: BombBot) -> None:
    await bot.add_cog(Owner(bot))