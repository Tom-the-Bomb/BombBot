from __future__ import annotations

from typing import Optional, Final, TYPE_CHECKING
from io import BytesIO, StringIO
import contextlib
import difflib

import discord
from discord.ext import commands

from PIL import Image
from jishaku.codeblocks import codeblock_converter
from fstop import Runner

if TYPE_CHECKING:
    from ..utils.context import BombContext
    from ..bot import BombBot

class Owner(commands.Cog):
    """Owner only utility commands"""

    def __init__(self, bot: BombBot) -> None:
        self.bot = bot
        self.runner: Final[Runner] = Runner(reset_after_execute=True)

    async def cog_check(self, ctx: BombContext) -> bool:
        return await ctx.bot.is_owner(ctx.author)

    def get_extension(self, extension: str, extensions: Optional[list[str]] = None) -> Optional[str]:
        extension = extension.lower().strip()

        if not extensions:
            extensions = tuple(self.bot.extensions.keys())

        if extension in extensions:
            return extension
        else:
            if matches := (
                [entry for entry in extensions if extension in entry] or
                difflib.get_close_matches(extension, extensions)
            ):
                return matches[0]
            else:
                shortened_exts = [entry.split('.')[-1].lower() for entry in extensions]

                if extension in shortened_exts:
                    return extensions[shortened_exts.index(extension)]
                elif matches := difflib.get_close_matches(extension, shortened_exts):
                    return extensions[shortened_exts.index(matches[0])]
                else:
                    return None

    @commands.command(name='fstop', aliases=('fs',))
    async def run_fstop(self, ctx: BombContext, *, code: codeblock_converter) -> None:

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
            await ctx.send(f'```py\n{content}\n```')
        else:
            with Image.open(BytesIO(output.getvalue())) as img:
                ext = img.format.lower()
            await ctx.send(file=discord.File(output, f'output.{ext}'))

    @commands.command(name='load')
    async def load(self, ctx: BombContext, *, extension: str) -> None:
        abs_extension = self.get_extension(extension, ctx.bot.all_extensions)

        if not abs_extension:
            await ctx.send(f'No extension or (similar extensions to {extension}) found')
        else:
            await ctx.bot.load_extension(abs_extension)
            await ctx.send(f'`➡️ {abs_extension}` loaded successfully')

    @commands.command(name='unload')
    async def unload(self, ctx: BombContext, *, extension: str) -> None:
        abs_extension = self.get_extension(extension)

        if not abs_extension:
            await ctx.send(f'No extension or (similar extensions to {extension}) found')
        else:
            await ctx.bot.unload_extension(abs_extension)
            await ctx.send(f'`⬅️ {abs_extension}` unloaded successfully')

    @commands.command(name='reload')
    async def reload(self, ctx: BombContext, *, extension: str) -> None:
        abs_extension = self.get_extension(extension)

        if not abs_extension:
            await ctx.send(f'No extension or (similar extensions to {extension}) found')
        else:
            await ctx.bot.reload_extension(abs_extension)
            await ctx.send(f'`🔁 {abs_extension}` reloaded successfully')

async def setup(bot: BombBot) -> None:
    await bot.add_cog(Owner(bot))