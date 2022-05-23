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
        self._cooldown = commands.CooldownMapping.from_cooldown(1, 7, commands.BucketType.user)

    async def cog_check(self, ctx: BombContext) -> bool:
        if await ctx.bot.is_owner(ctx.author):
            return True
            
        cooldown = self._cooldown.get_bucket(ctx.message)
        if not cooldown:
            return True
        retry_after = cooldown.update_rate_limit()

        if retry_after:
            raise commands.CommandOnCooldown(cooldown, retry_after, commands.BucketType.user)
        return True

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

    @commands.command(name='fisheye', aliases=('sphere',))
    async def _fisheye(self, ctx: BombContext, image: str = None) -> None:
        return await do_command(ctx, image, func=fisheye)

    @commands.command(name='bomb')
    async def _bomb(self, ctx: BombContext, image: str = None) -> None:
        return await do_command(ctx, image, func=bomb)
    
    # pil functions

    @commands.command(name='type', aliases=('write',))
    async def _type(self, ctx: BombContext, *, text: str = None) -> None:

        if not text:
            if ref := ctx.message.reference:
                text = ref.resolved.content
            else:
                text = 'Specify something for me to type out next time...'
        return await do_command(ctx, text, func=type_gif, duration=20)

    @commands.command(name='image-info', aliases=('info', 'imginfo', 'img-info'))
    async def _image_info(self, ctx: BombContext, *, image: str = None) -> None:
        file, embed = await image_info(ctx, image)
        await ctx.send(embed=embed, file=file)
        

async def setup(bot: BombBot) -> None:
    from importlib import reload
    from bot.utils.imaging import pil_functions
    from bot.utils.imaging import wand_functions

    reload(pil_functions)
    reload(wand_functions)
    
    await bot.add_cog(Imaging(bot))