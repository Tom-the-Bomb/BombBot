from __future__ import annotations

from typing import ClassVar, Optional, TypeAlias, TYPE_CHECKING
from io import BytesIO

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from ..context import BombContext

    Argument: TypeAlias = discord.Member | discord.User | discord.PartialEmoji | bytes


__all__: tuple[str, ...] = (
    'ImageTooLarge',
    'DefaultEmojiConverter',
    'UrlConverter',
    'ImageConverter',
)

class ImageTooLarge(commands.CheckFailure):
    pass

class DefaultEmojiConverter(commands.Converter):

    async def convert(self, ctx: BombContext, argument: str) -> bytes:
        emoji = await ctx.bot.get_twemoji(argument)
        
        if not emoji:
            raise commands.BadArgument('Invalid Emoji')
        else:
            return emoji

class UrlConverter(commands.Converter):

    async def convert(self, ctx: BombContext, argument: str) -> bytes:
        
        bad_arg = commands.BadArgument('Invalid URL')
        argument = argument.strip('<>')
        try:
            async with ctx.bot.session.get(argument) as r:
                if r.ok and r.content_type.startswith('image/'):
                    return await r.read()
                else:
                    raise bad_arg
        except Exception:
            raise bad_arg

class ImageConverter:
    ctx: BombContext
    _converters: ClassVar[tuple[type[commands.Converter], ...]] = (
        commands.MemberConverter,
        commands.UserConverter,
        commands.PartialEmojiConverter,
        DefaultEmojiConverter,
        UrlConverter,
    )

    def check_size(self, byt: bytes, *, max_size: int = 8_000_000) -> None:
        MIL = 1_000_000
        if (size := byt.__sizeof__()) > max_size:
            raise ImageTooLarge(
                f'The size of the provided image (`{size / MIL:.2f} MB`) '
                f'exceeds the limit of `{max_size / MIL} MB`'
            )

    async def converted_to_buffer(self, source: Argument) -> bytes:
        if isinstance(source, discord.Member | discord.User):
            source = await source.display_avatar.read()

        elif isinstance(source, discord.PartialEmoji):
            source = await source.read()

        return source

    async def get_attachments(self, message: Optional[discord.Message] = None) -> Optional[bytes]:
        source = None
        message = message or self.ctx.message

        if files := message.attachments:
            source = await self.get_file_image(files)
        
        if (st := message.stickers) and source is None:
            source = await self.get_sticker_image(st)

        if (embeds := message.embeds) and source is None:
            for embed in embeds:
                if img := embed.image.url or embed.thumbnail.url:
                    try:
                        source = await UrlConverter().convert(self.ctx, img)
                        break
                    except commands.BadArgument:
                        continue
        return source
 
    async def get_sticker_image(self, stickers: list[discord.StickerItem]) -> Optional[bytes]:
        sticker = stickers[0]

        if not sticker.format == discord.StickerFormatType.lottie:
            try:
                return await UrlConverter().convert(self.ctx, sticker.url)
            except commands.BadArgument:
                return None

    async def get_file_image(self, files: list[discord.Attachment]) -> Optional[bytes]:
        file = files[0]

        if file.content_type and file.content_type.startswith('image/'):
            return await file.read()

    async def try_to_convert(self, argument: str) -> Optional[bytes]:

        for converter in self._converters:
            try:
                source = await converter().convert(self.ctx, argument)
            except commands.BadArgument:
                continue
            else:
                break
        else:
            return None

        return await self.converted_to_buffer(source)

    async def get_image(self, ctx: BombContext, argument: Optional[str]) -> BytesIO:
        self.ctx = ctx
        source = None

        if argument is not None:
            source = await self.try_to_convert(argument)

        if source is None:
            source = await self.get_attachments()
        
            if (ref := self.ctx.message.reference) and source is None:
                ref = ref.resolved

                if not isinstance(ref, discord.DeletedReferencedMessage) and ref:
                    source = await self.get_attachments(ref)

                    if source is None and ref.content:
                        source = await self.try_to_convert(ref.content.split()[0])

        if source is None:
            source = await self.ctx.author.display_avatar.read()

        self.check_size(source)
        return BytesIO(source)