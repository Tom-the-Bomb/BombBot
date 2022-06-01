from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Literal
import textwrap

from discord.ext import commands

from bot.utils.imaging import do_command, ImageConverter

from bot.utils.imaging.flags import *
from bot.utils.imaging.pil_functions import *
from bot.utils.imaging.wand_functions import *
from bot.utils.imaging.cv_functions import *

if TYPE_CHECKING:
    from bot.bot import BombBot
    from bot.utils.context import BombContext

class Imaging(commands.Cog):
    """Contains numerous image processing commands
    utilizing `ImageMagick`, `pillow` and `OpenCV`
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
    async def _blur(self, ctx: BombContext, image: Optional[ImageConverter], *, options: GeneralIntensity) -> None:
        """Blurs the provided image"""
        return await do_command(ctx, image, func=blur, intensity=options.intensity)

    @commands.command(name='emboss')
    async def _emboss(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Blurs the provided image"""
        return await do_command(ctx, image, func=emboss)

    @commands.command(name='invert')
    async def _invert(self, ctx: BombContext, image: Optional[ImageConverter], *, options: Channels) -> None:
        """Inverts the provided image"""
        return await do_command(ctx, image, func=invert, channel=options.channel)

    @commands.command(name='colorize', aliases=('recolor', 'tint'))
    async def _colorize(self, ctx: BombContext, image: Optional[ImageConverter], *, options: ColorFlag) -> None:
        """Colorizes an image to the provided color"""
        return await do_command(ctx, image, func=colorize, color=options.color)

    @commands.command(name='vignette')
    async def _vignette(self, ctx: BombContext, image: Optional[ImageConverter], *, options: GeneralIntensity) -> None:
        """Creates a vignette on the provided image of the provided size"""
        return await do_command(ctx, image, func=vignette, size=options.intensity)

    @commands.command(name='wave')
    async def _wave(self, ctx: BombContext, image: Optional[ImageConverter], *, options: GeneralIntensity) -> None:
        """Makes the provided image all wavy"""
        return await do_command(ctx, image, func=wave, count=options.intensity)

    @commands.command(name='polaroid')
    async def _polaroid(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Creates a polaroid image frame on the image"""
        return await do_command(ctx, image, func=polaroid)

    @commands.command(name='fuzz')
    async def _fuzz(self, ctx: BombContext, image: Optional[ImageConverter], *, options: GeneralIntensity) -> None:
        """Makes the provided image all fuzzy"""
        return await do_command(ctx, image, func=fuzz, intensity=options.intensity)

    @commands.command(name='sketch')
    async def _sketch(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Sketches out the provided image"""
        return await do_command(ctx, image, func=sketch)

    @commands.command(name='replace-color', aliases=('replacecolor', 'replace'))
    async def _replace_color(self, ctx: BombContext, image: Optional[ImageConverter], *, options: ReplaceColors) -> None:
        """Replaces the all instances of the color `target` 
        or any color similar by 20% with the color: `to`
        """
        return await do_command(ctx, image, func=replace_color, target=options.target, to=options.to)

    @commands.command(name='paint')
    async def _paint(self, ctx: BombContext, image: Optional[ImageConverter], *, options: GeneralIntensity) -> None:
        """Paints out the image using oil paint"""
        return await do_command(ctx, image, func=paint, spread=options.intensity)

    @commands.command(name='charcoal')
    async def _charcoal(self, ctx: BombContext, image: Optional[ImageConverter], *, options: CharcoalIntensity) -> None:
        """Draws out the image using charcoal"""
        return await do_command(ctx, image, func=charcoal, intensity=options.intensity)

    @commands.command(name='threshold')
    async def _threshold(self, ctx: BombContext, image: Optional[ImageConverter], *, options: Threshold) -> None:
        """Thresholds the image"""
        return await do_command(ctx, image, func=threshold, threshold=options.threshold, channel=options.channel)

    @commands.command(name='noise')
    async def _noise(self, ctx: BombContext, image: Optional[ImageConverter], *, options: GeneralIntensity) -> None:
        """Adds noise onto an image"""
        return await do_command(ctx, image, func=noise, amount=options.intensity)

    @commands.command(name='posterize', aliases=('poster',))
    async def _posterize(self, ctx: BombContext, image: Optional[ImageConverter], *, options: GeneralIntensity) -> None:
        """Posterizes the provided image"""
        return await do_command(ctx, image, func=posterize, static=True, layers=options.intensity)

    @commands.command(name='arc')
    async def _arc(self, ctx: BombContext, image: Optional[ImageConverter], *, options: Degree) -> None:
        """Distorts the provided image in the shape of an arc"""
        return await do_command(ctx, image, func=arc, degree=options.degree)

    @commands.group(name='floor', aliases=('tile', 'tiles'), invoke_without_command=True)
    async def _floor(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Makes a tiled floor with the provided image"""
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
    async def _solarize(self, ctx: BombContext, image: Optional[ImageConverter], *, options: Threshold) -> None:
        """solarizes the provided image, resulting in a burnt effect"""
        return await do_command(ctx, image, func=solarize, threshold=options.threshold, channel=options.channel)
    
    @commands.command(name='spread-cards', aliases=('cards', 'spread', 'spreadcards'))
    async def _spread_cards(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """Spreads the provided image out like playing cards"""
        return await do_command(ctx, image, func=spread_cards)

    @commands.command(name='lego')
    async def _lego(self, ctx: BombContext, image: Optional[ImageConverter], *, options: LegoSize) -> None:
        """Builds the provided image with lego pieces"""
        return await do_command(ctx, image, func=lego, size=options.size)

    @commands.command(name='minecraft', aliases=('mc',))
    async def _minecraft(self, ctx: BombContext, image: Optional[ImageConverter], *, options: BlockSize) -> None:
        """Builds the provided image with minecraft blocks"""
        return await do_command(ctx, image, func=minecraft, size=options.size)

    @commands.command(name='cube')
    async def cube(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """Wraps the provided image on a cube"""
        return await do_command(ctx, image, func=cube)

    # pil functions

    @commands.command(name='matrix', aliases=('code', 'ascii'))
    async def _matrix(self, ctx: BombContext, image: Optional[ImageConverter], *, options: BlockSize) -> None:
        """Generates a matrix gif with the provided image"""
        return await do_command(ctx, image, func=matrix, size=options.size)

    @commands.command(name='flip')
    async def _flip(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """Flips the provided image on it's x-axis"""
        return await do_command(ctx, image, func=flip)

    @commands.command(name='mirror')
    async def _mirror(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """Flips the provided image on it's y-axis"""
        return await do_command(ctx, image, func=mirror)

    @commands.command(name='contour')
    async def _contour(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """returns only the outline & contour of the provided image"""
        return await do_command(ctx, image, func=contour)

    @commands.command(name='spin')
    async def _spin(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """returns only the outline & contour of the provided image"""
        return await do_command(ctx, image, func=spin)

    @commands.command(name='type', aliases=('write',))
    async def _type(self, ctx: BombContext, *, options: str = None) -> None:
        """Types out the provided text in an animation"""
        MAX_SIZE = 1000
        if not text:
            if ref := ctx.message.reference:
                text = ref.resolved.content
            else:
                text = 'Specify something for me to type out next time...'
        if len(text) > MAX_SIZE:
            text = textwrap.shorten(text, width=MAX_SIZE + 3, placeholder=' ...')
        return await do_command(ctx, text, func=type_gif, duration=20)

    @commands.command(name='lines', aliases=('line', 'streaks'))
    async def _lines(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """Makes the provided image all streaky and stuff"""
        return await do_command(ctx, image, func=lines)

    @commands.command(name='balls', aliases=('ball', 'bubbles', 'circles'))
    async def _balls(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """Builds the provided image with balls"""
        return await do_command(ctx, image, func=balls)

    @commands.command(name='squares', aliases=('square', 'boxes', 'blocks'))
    async def _squares(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """Builds the provided image with squares"""
        return await do_command(ctx, image, func=squares)

    @commands.command(name='letters', aliases=('letter',))
    async def _letters(self, ctx: BombContext, image: Optional[ImageConverter]) -> None:
        """Builds the provided image with random letters"""
        return await do_command(ctx, image, func=letters)

    @commands.command(name='image-info', aliases=('info', 'imginfo', 'img-info', 'iminfo'))
    async def _image_info(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Displays basic information about the provided image"""
        embed, *files = await image_info(ctx, image)
        await ctx.send(embed=embed, files=files)

    # opencv-python functions

    @commands.command(name='invert-scan', aliases=('invertscan', 'scaninvert', 'scan-invert'))
    async def _invert_scan(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Inverts the image but as part of a scanning animation"""
        return await do_command(ctx, image, func=invert_scan)

    @_floor.command(name='speed', aliases=('fast',))
    async def _speed_floor(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Makes a tiled floor with the provided image, but utilizes a faster algorithm
        but at the same time producing slightly poorer quality results when compared to the parent command
        """
        return await do_command(ctx, image, func=cv_floor)

    @commands.command(name='canny', aliases=('edgedetect', 'edge-detect', 'edges'))
    async def _canny(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Runs a canny algorithm on an image; edge-detection"""
        return await do_command(ctx, image, func=canny)

    @commands.command(name='colordetect', aliases=('color-detect', 'cd'))
    async def _colordetect(self, ctx: BombContext, image: Optional[ImageConverter], *, options: ColorFlag) -> None:
        """Detects a certain color within the image"""
        return await do_command(ctx, image, func=colordetect, color=options.color)

    @commands.command(name='cornerdetect', aliases=('corner-detect', 'corners'))
    async def _cornerdetect(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Detects corners within the image"""
        return await do_command(ctx, image, func=cornerdetect)
    
    @commands.command(name='dilate', aliases=('fatten', 'blowup', 'blow'))
    async def _dilate(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Dilates an image outwards"""
        return await do_command(ctx, image, func=dilate)

    @commands.command(name='cartoon')
    async def _cartoon(self, ctx: BombContext, *, image: Optional[ImageConverter]) -> None:
        """Cartoonifies an image"""
        return await do_command(ctx, image, func=cartoon)
        

async def setup(bot: BombBot) -> None:
    from importlib import reload
    from bot.utils.imaging import pil_functions
    from bot.utils.imaging import wand_functions
    from bot.utils.imaging import cv_functions

    reload(pil_functions)
    reload(wand_functions)
    reload(cv_functions)
    
    await bot.add_cog(Imaging(bot))