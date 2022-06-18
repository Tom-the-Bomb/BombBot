from __future__ import annotations

from typing import TYPE_CHECKING
import platform
import time

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from ..bot import BombBot
    from ..utils.context import BombContext

class General(commands.Cog):
    """Contains various "meta" commands, information about the bot
    general stuff etc.
    """

    def __init__(self, bot: BombBot) -> None:
        self.bot = bot

    @commands.command(name='botinfo')
    async def botinfo(self, ctx: BombContext) -> None:
        cmds = await ctx.bot.help_command.filter_commands(ctx.bot.walk_commands())

        if not (owner_id := ctx.bot.owner_id):
            app = await ctx.bot.application_info()
            owner_id = app.owner.id

        rest_start = time.perf_counter()
        owner = await ctx.bot.fetch_user(owner_id)
        rest_end = time.perf_counter()

        d, h, m, s = ctx.bot.get_uptime()

        cs = ctx.bot.code_stats
        fc, lc, cl, fn, co = cs['files'], cs['lines'], cs['classes'], cs['funcs'], cs['coros']
        
        embed = discord.Embed(
            timestamp=discord.utils.utcnow(),
            color=ctx.bot.EMBED_COLOR,
            description=(
                f'`{ctx.bot.user}` | `{ctx.bot.user.id}`\n\n'
                f'[**Invite Me**]({ctx.bot.invite_url})\n'
                '\n```yml\n'
                f'Developer:  {owner}\n'
                f'Written-in: Python {platform.python_version()}\n'
                f'Library:    {discord.__name__}.py {discord.__version__}\n'
                f'WS-latency: {ctx.bot.latency * 1000:.1f} ms\n'
                f'REST-latency:  {(rest_end - rest_start) * 1000:.1f} ms\n'
                f'Cog-count:     {len(ctx.bot.cogs)}\n'
                f'Command-count: {len(cmds)}\n'
                f'Guild-count: {len(ctx.bot.guilds)}\n'
                f'User-count:  {sum(g.member_count for g in ctx.bot.guilds)}\n'
                f'Unique-user-count: {len(set(ctx.bot.users))}\n\n'
                f'Uptime:\n  - Days:  {d}\n  - Hours: {h}\n  - Mins:  {m}\n  - Secs:  {s}\n\n'
                f'Code-stats:\n  - Files: {fc:,}\n  - Lines: {lc:,}\n  - Classes: {cl:,}\n  - Funcs: {fn:,}\n  - Coros: {co:,}\n```'
            )
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=ctx.bot.user.avatar.url)
        await ctx.reply(embed=embed)

async def setup(bot: BombBot) -> None:
    await bot.add_cog(General(bot))