from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Literal

from discord.ext import commands

from bot.utils.imaging import do_command, ImageConverter, ColorConverter
from bot.utils.imaging.flags import *
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
    async def _blur(self, ctx: BombContext, image: Optional[ImageConverter], *, intensity: GeneralIntensity) -> None:
        """Blurs the provided image"""
        return await do_command(ctx, image, func=blur, intensity=intensity.intensity)

    @commands.command(name='emboss')
    async def _emboss(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Blurs the provided image"""
        return await do_command(ctx, image, func=emboss)

    @commands.command(name='invert')
    async def _invert(self, ctx: BombContext, image: Optional[ImageConverter], *, channel: Channels) -> None:
        """Inverts the provided image"""
        return await do_command(ctx, image, func=invert, channel=channel.channel)

    @commands.command(name='colorize', aliases=('recolor', 'tint'))
    async def _colorize(self, ctx: BombContext, image: Optional[ImageConverter], *, color: ColorConverter) -> None:
        """Colorizes an image to the provided color"""
        return await do_command(ctx, image, func=colorize, color=color)

    @commands.command(name='vignette')
    async def _vignette(self, ctx: BombContext, image: Optional[ImageConverter], *, intensity: GeneralIntensity) -> None:
        """Creates a vignette on the provided image of the provided size"""
        return await do_command(ctx, image, func=vignette, size=intensity.intensity)

    @commands.command(name='wave')
    async def _wave(self, ctx: BombContext, image: Optional[ImageConverter], *, intensity: GeneralIntensity) -> None:
        """Makes the provided image all wavy"""
        return await do_command(ctx, image, func=wave, count=intensity.intensity)

    @commands.command(name='polaroid')
    async def _polaroid(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Creates a polaroid image frame on the image"""
        return await do_command(ctx, image, func=polaroid)

    @commands.command(name='fuzz')
    async def _fuzz(self, ctx: BombContext, image: Optional[ImageConverter], *, intensity: GeneralIntensity) -> None:
        """Makes the provided image all fuzzy"""
        return await do_command(ctx, image, func=fuzz, intensity=intensity.intensity)

    @commands.command(name='sketch')
    async def _sketch(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Sketches out the provided image"""
        return await do_command(ctx, image, func=sketch)

    @commands.command(name='replace-color', aliases=('replacecolor', 'replace'))
    async def _replace_color(self, ctx: BombContext, image: Optional[ImageConverter], target: ColorConverter, *, to: ColorConverter) -> None:
        """Sketches out the provided image"""
        return await do_command(ctx, image, func=replace_color, target=target, to=to)

    @commands.command(name='paint')
    async def _paint(self, ctx: BombContext, image: Optional[ImageConverter], *, intensity: GeneralIntensity) -> None:
        """Paints out the image using oil paint"""
        return await do_command(ctx, image, func=paint, spread=intensity.intensity)

    @commands.command(name='charcoal')
    async def _charcoal(self, ctx: BombContext, image: Optional[ImageConverter], *, intensity: CharcoalIntensity) -> None:
        """Draws out the image using charcoal"""
        return await do_command(ctx, image, func=charcoal, intensity=intensity.intensity)

    @commands.command(name='posterize', aliases=('poster',))
    async def _posterize(self, ctx: BombContext, image: Optional[ImageConverter], *, intensity: GeneralIntensity) -> None:
        """Posterizes the provided image"""
        return await do_command(ctx, image, func=posterize, static=True, layers=intensity.intensity)

    @commands.command(name='arc')
    async def _arc(self, ctx: BombContext, image: Optional[ImageConverter], *, degree: Degree) -> None:
        """Distorts the provided image in the shape of an arc"""
        return await do_command(ctx, image, func=arc, degree=degree.degree)

    @commands.command(name='floor')
    async def _floor(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Makes tiled floor with the provided image"""
        return await do_command(ctx, image, func=floor)

    @commands.command(name='gallery')
    async def _gallery(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Returns a sliding gallery / conveyor belt type thing with the provided image"""
        return await do_command(ctx, image, func=slide)

    @commands.command(name='bulge')
    async def _bulge(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Makes the center of the image bulge out dramatically"""
        return await do_command(ctx, image, func=bulge)

    @commands.command(name='swirl')
    async def _swirl(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Swirls the provided image back and forth"""
        return await do_command(ctx, image, func=swirl)

    @commands.command(name='turn')
    async def _turn(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """spins the provided image around and around, bouncing off of the image boundaries"""
        return await do_command(ctx, image, func=turn)

    @commands.command(name='fisheye', aliases=('sphere',))
    async def _fisheye(self, ctx: BombContext, image: Optional[ImageConverter], shade: Optional[Literal['--no-shade']]) -> None:
        """Distorts the provided image with fisheye, basically making the image look sphere like
        Additionally a shading overlay is put on top of the image to give it a more 3D look

        The optional flag: `--no-shade` can be passed to tell it to not shade the image
        """
        return await do_command(ctx, image, func=fisheye, shade=not shade)

    @commands.command(name='bomb')
    async def _bomb(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """Returns a GIF with an explosion animation extended onto the provided image"""
        return await do_command(ctx, image, func=bomb)

    @commands.command(name='cycle-colors', aliases=('cycle',))
    async def _cycle_colors(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """Cycle's the provided image's color mapping"""
        return await do_command(ctx, image, func=cycle_colors)

    @commands.command(name='huerotate', aliases=('rotatehue',))
    async def _hue_rotate(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """rotates around and changes the hue of the provided image"""
        return await do_command(ctx, image, func=huerotate)

    @commands.command(name='solarize', aliases=('solar',))
    async def _solarize(self, ctx: BombContext, image: Optional[ImageConverter], *, threshold: SolarizeThreshold) -> None:
        """solarizes the provided image, resulting in a burnt effect"""
        return await do_command(ctx, image, func=solarize, threshold=threshold.threshold, channel=threshold.channel)
    
    @commands.command(name='spread-cards', aliases=('cards', 'spread'))
    async def _spread_cards(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """Spreads the provided image out like playing cards"""
        return await do_command(ctx, image, func=spread_cards)

    @commands.command(name='lego')
    async def _lego(self, ctx: BombContext, image: Optional[ImageConverter], *, size: LegoSize) -> None:
        """Builds the provided image with lego pieces"""
        return await do_command(ctx, image, func=lego, size=size.size)

    @commands.command(name='minecraft', aliases=('mc',))
    async def _minecraft(self, ctx: BombContext, image: Optional[ImageConverter], *, size: McSize) -> None:
        """Builds the provided image with minecraft blocks"""
        return await do_command(ctx, image, func=minecraft, size=size.size)

    @commands.command(name='cube')
    async def cube(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """Wraps the provided image on a cube"""
        return await do_command(ctx, image, func=cube)

    # pil functions

    @commands.command(name='flip')
    async def _flip(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """Flips the provided image on it's x-axis"""
        return await do_command(ctx, image, func=flip)

    @commands.command(name='mirror')
    async def _mirror(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """Flips the provided image on it's y-axis"""
        return await do_command(ctx, image, func=mirror)

    @commands.command(name='contour', aliases=('lines',))
    async def _contour(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
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
    async def _image_info(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Displays basic information about the provided image"""
        embed, *files = await image_info(ctx, image)
        await ctx.send(embed=embed, files=files)
        

async def setup(bot: BombBot) -> None:
    from importlib import reload
    from bot.utils.imaging import pil_functions
    from bot.utils.imaging import wand_functions

    reload(pil_functions)
    reload(wand_functions)
    
    await bot.add_cog(Imaging(bot))