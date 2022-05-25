from __future__ import annotations

from typing import ClassVar, Optional, TypeAlias, TYPE_CHECKING
from io import BytesIO

import discord
from discord.ext import commands
from wand.color import Color

from ..helpers import Regexes

if TYPE_CHECKING:
    from aiohttp import ClientResponse
    from ..context import BombContext

    Argument: TypeAlias = discord.Member | discord.User | discord.PartialEmoji | bytes


__all__: tuple[str, ...] = (
    'ImageTooLarge',
    'InvalidColor',
    'ColorConverter',
    'DefaultEmojiConverter',
    'UrlConverter',
    'ImageConverter',
)

class ImageTooLarge(commands.CheckFailure):
    pass

class InvalidColor(commands.BadArgument):
    pass

class ColorConverter(commands.Converter):

    async def convert(self, ctx: BombContext, argument: str) -> Color:
        try:
            return Color(argument.strip())
        except ValueError as exc:
            raise InvalidColor(f'{argument} is an invalid color') from exc

class DefaultEmojiConverter(commands.Converter):

    async def convert(self, ctx: BombContext, argument: str) -> bytes:
        emoji = await ctx.bot.get_twemoji(argument)
        
        if not emoji:
            raise commands.BadArgument('Invalid Emoji')
        else:
            return emoji

class UrlConverter(commands.Converter):

    async def find_tenor_gif(self, ctx: BombContext, response: ClientResponse) -> bytes:
        bad_arg = commands.BadArgument('An Error occured when fetching the tenor GIF')
        try:
            content = await response.text()
            if match := Regexes.TENOR_GIF_REGEX.search(content):
                async with ctx.bot.session.get(match.group()) as gif:
                    if gif.ok:
                        return await gif.read()
                    else:
                        raise bad_arg
            else:
                raise bad_arg
        except Exception:
            raise bad_arg

    async def convert(self, ctx: BombContext, argument: str) -> bytes:
        
        bad_arg = commands.BadArgument('Invalid URL')
        argument = argument.strip('<>')
        try:
            async with ctx.bot.session.get(argument) as r:
                if r.ok:
                    if r.content_type.startswith('image/'):
                        return await r.read()
                    elif Regexes.TENOR_PAGE_REGEX.fullmatch(argument):
                        return await self.find_tenor_gif(ctx, r)
                    else:
                        raise bad_arg
                else:
                    raise bad_arg
        except Exception:
            raise bad_arg

class ImageConverter(commands.Converter):
    """
    ImageConverter

    A class for fetching and resolving images within a command, it attempts to fetch, (in order):
        - Member from the command argument, then User if failed
        - A Guild Emoji from the command argument, then default emoji if failed
        - An image url, content-type must be of `image/xx`
        - An attachment from the invocation message
        - A sticker from the invocation message

        If all above fails, it repeats the above for references (replies)
        and also searches for embed thumbnails / images in references

    Raises
    ------
    ImageTooLarge
        The resolved image is too large, possibly a decompression bomb?
    commands.BadArgument
        Failed to fetch anything
    """
    _converters: ClassVar[tuple[type[commands.Converter], ...]] = (
        commands.MemberConverter,
        commands.UserConverter,
        commands.PartialEmojiConverter,
        DefaultEmojiConverter,
        UrlConverter,
    )

    def check_size(self, byt: bytes, *, max_size: int = 15_000_000) -> None:
        MIL = 1_000_000
        if (size := byt.__sizeof__()) > max_size:
            del byt
            raise ImageTooLarge(
                f'The size of the provided image (`{size / MIL:.2f} MB`) '
                f'exceeds the limit of `{max_size / MIL} MB`'
            )

    async def converted_to_buffer(self, source: Argument) -> bytes:
        if isinstance(source, (discord.Member, discord.User)):
            source = await source.display_avatar.read()

        elif isinstance(source, discord.PartialEmoji):
            source = await source.read()

        return source

    async def get_attachments(self, ctx: BombContext, message: Optional[discord.Message] = None) -> Optional[bytes]:
        source = None
        message = message or ctx.message

        if files := message.attachments:
            source = await self.get_file_image(files)
        
        if (st := message.stickers) and source is None:
            source = await self.get_sticker_image(ctx, st)

        if (embeds := message.embeds) and source is None:
            for embed in embeds:
                if img := embed.image.url or embed.thumbnail.url:
                    try:
                        source = await UrlConverter().convert(ctx, img)
                        break
                    except commands.BadArgument:
                        continue
        return source
 
    async def get_sticker_image(self, ctx: BombContext, stickers: list[discord.StickerItem]) -> Optional[bytes]:
        for sticker in stickers:
            if sticker.format is not discord.StickerFormatType.lottie:
                try:
                    return await UrlConverter().convert(ctx, sticker.url)
                except commands.BadArgument:
                    continue

    async def get_file_image(self, files: list[discord.Attachment]) -> Optional[bytes]:
        for file in files:
            if file.content_type and file.content_type.startswith('image/'):
                return await file.read()

    async def convert(self, ctx: BombContext, argument: str, *, raise_on_failure: bool = True) -> Optional[bytes]:

        for converter in self._converters:
            try:
                source = await converter().convert(ctx, argument)
            except commands.BadArgument:
                continue
            else:
                break
        else:
            if raise_on_failure:
                raise commands.BadArgument('Failed to fetch an image from argument')

        return await self.converted_to_buffer(source)

    async def get_image(self, ctx: BombContext, source: Optional[str | bytes], *, max_size: int = 15_000_000) -> BytesIO:

        if source is None:
            source = await self.get_attachments(ctx)
        
            if (ref := ctx.message.reference) and source is None:
                ref = ref.resolved

                if not isinstance(ref, discord.DeletedReferencedMessage) and ref:
                    source = await self.get_attachments(ctx, ref)

                    if source is None and ref.content:
                        source = await self.convert(ctx, ref.content.split()[0], raise_on_failure=False)

        if source is None:
            source = await ctx.author.display_avatar.read()

        self.check_size(source, max_size=max_size)
        return BytesIO(source)