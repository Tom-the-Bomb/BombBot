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
    @commands.command(name='blur')
    async def _blur(self, ctx: BombContext, *, image: str = None) -> None:
        """Blurs the provided image"""
        return await do_command(ctx, image, func=blur)

    @commands.command(name='emboss')
    async def _emboss(self, ctx: BombContext, *, image: str = None) -> None:
        """Blurs the provided image"""
        return await do_command(ctx, image, func=emboss)

    @commands.command(name='invert')
    async def _invert(self, ctx: BombContext, *, image: str = None) -> None:
        """Inverts the provided image"""
        return await do_command(ctx, image, func=invert)

    @commands.command(name='arc')
    async def _arc(self, ctx: BombContext, *, image: str = None) -> None:
        """Distorts the provided image in the shape of a 180-deg arc: a semicircle"""
        return await do_command(ctx, image, func=arc)

    @commands.command(name='floor')
    async def _floor(self, ctx: BombContext, *, image: str = None) -> None:
        """Makes tiled floor with the provided image"""
        return await do_command(ctx, image, func=floor)

    @commands.command(name='gallery')
    async def _gallery(self, ctx: BombContext, *, image: str = None) -> None:
        """Returns a sliding gallery / conveyor belt type thing with the provided image"""
        return await do_command(ctx, image, func=slide)

    @commands.command(name='bulge')
    async def _bulge(self, ctx: BombContext, *, image: str = None) -> None:
        """Makes the center of the image bulge out dramatically"""
        return await do_command(ctx, image, func=bulge)

    @commands.command(name='swirl')
    async def _swirl(self, ctx: BombContext, *, image: str = None) -> None:
        """Swirls the provided image back and forth"""
        return await do_command(ctx, image, func=swirl)

    @commands.command(name='turn')
    async def _turn(self, ctx: BombContext, *, image: str = None) -> None:
        """spins the provided image around and around, bouncing off of the image boundaries"""
        return await do_command(ctx, image, func=turn)

    @commands.command(name='fisheye', aliases=('sphere',))
    async def _fisheye(self, ctx: BombContext, image: str = None) -> None:
        """Distorts the provided image with fisheye, basically making the image look sphere like
        Additionally a shading overlay is put on top of the image to give it a more 3D look
        """
        return await do_command(ctx, image, func=fisheye)

    @commands.command(name='bomb')
    async def _bomb(self, ctx: BombContext, image: str = None) -> None:
        """Returns a GIF with an explosion animation extended onto the provided image"""
        return await do_command(ctx, image, func=bomb)

    @commands.command(name='cycle-colors', aliases=('cycle',))
    async def _cycle_colors(self, ctx: BombContext, image: str = None) -> None:
        """Cycle's the provided image's color mapping"""
        return await do_command(ctx, image, func=cycle_colors)

    @commands.command(name='huerotate', aliases=('rotatehue',))
    async def _hue_rotate(self, ctx: BombContext, image: str = None) -> None:
        """rotates around and changes the hue of the provided image"""
        return await do_command(ctx, image, func=huerotate)

    @commands.command(name='solarize', aliases=('solar',))
    async def _solarize(self, ctx: BombContext, image: str = None) -> None:
        """solarizes the provided image, resulting in a burnt effect"""
        return await do_command(ctx, image, func=solarize)
    
    @commands.command(name='spread-cards', aliases=('cards', 'spread'))
    async def _spread_cards(self, ctx: BombContext, image: str = None) -> None:
        """Spreads the provided image out like playing cards"""
        return await do_command(ctx, image, func=spread_cards)

    @commands.command(name='lego')
    async def _lego(self, ctx: BombContext, image: str = None) -> None:
        """Builds the provided image with lego pieces"""
        return await do_command(ctx, image, func=lego)

    @commands.command(name='minecraft', aliases=('mc',))
    async def _minecraft(self, ctx: BombContext, image: str = None) -> None:
        """Builds the provided image with minecraft blocks"""
        return await do_command(ctx, image, func=minecraft)

    # pil functions

    @commands.command(name='flip')
    async def _flip(self, ctx: BombContext, image: str = None) -> None:
        """Flips the provided image on it's x-axis"""
        return await do_command(ctx, image, func=flip)

    @commands.command(name='mirror')
    async def _mirror(self, ctx: BombContext, image: str = None) -> None:
        """Flips the provided image on it's y-axis"""
        return await do_command(ctx, image, func=mirror)

    @commands.command(name='contour', aliases=('lines',))
    async def _contour(self, ctx: BombContext, image: str = None) -> None:
        """returns only the outline & contour of the provided image"""
        return await do_command(ctx, image, func=contour)

    @commands.command(name='type', aliases=('write',))
    async def _type(self, ctx: BombContext, *, text: str = None) -> None:
        """Types out the provided text in an animation"""
        if not text:
            if ref := ctx.message.reference:
                text = ref.resolved.content
            else:
                text = 'Specify something for me to type out next time...'
        return await do_command(ctx, text, func=type_gif, duration=20)

    @commands.command(name='image-info', aliases=('info', 'imginfo', 'img-info', 'iminfo'))
    async def _image_info(self, ctx: BombContext, *, image: str = None) -> None:
        """Displays basic information about the provided image"""
        file, embed = await image_info(ctx, image)
        await ctx.send(embed=embed, file=file)
        

async def setup(bot: BombBot) -> None:
    from importlib import reload
    from bot.utils.imaging import pil_functions
    from bot.utils.imaging import wand_functions

    reload(pil_functions)
    reload(wand_functions)
    
    await bot.add_cog(Imaging(bot))