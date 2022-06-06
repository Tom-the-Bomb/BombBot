from typing import Optional, TypedDict, Any, Final
import pathlib
import json
import logging
import traceback
from math import ceil
from inspect import getdoc

import jishaku
import discord
from discord.ext import commands
from aiohttp import MultipartWriter, ClientSession
from wand.image import Image

from .utils.context import BombContext
from .utils.imaging.converter import ImageTooLarge, InvalidColor

class Config(TypedDict):
    TOKEN: str
    PREFIXES: list[str]

class BombBot(commands.Bot):
    """A multipurpose discord bot featuring numerous games and image processing command among many others
    """
    EMBED_COLOR: Final[int] = 0x2F3136

    def __init__(self, **options: Any) -> None:

        self.session: Optional[ClientSession] = None

        self.config: Config = self.load_config()
        self.default_prefixes: list[str] = self.config['PREFIXES']
        self.token: str = self.config['TOKEN']

        self.setup_logging()

        intents = discord.Intents.all()
        
        super().__init__(
            command_prefix=commands.when_mentioned_or(*self.default_prefixes),
            description=getdoc(self),
            intents=intents,
            case_insensitive=True, 
            status=discord.Status.idle,
            activity=discord.Game('beep boop'),
            **options,
        )

    @property
    def all_extensions(self) -> list[str]:
        exts = pathlib.Path('./bot/ext').glob('**/[!__]*.py')
        exts = ['.'.join(ext.parts).removesuffix('.py') for ext in exts]
        return exts

    def setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('discord')
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
        )
        logger.addHandler(handler)

        self.logger: logging.Logger = logger
        self.logger.info('--- INITIALIZED ---')
        
        return self.logger

    def load_config(self) -> Config:
        with open('config.json') as config:
            return json.load(config)

    def run(self, *args: Any, **kwargs: Any) -> None:
        token = kwargs.pop('token', self.token)
        reconnect = kwargs.pop('reconnect', True)
        return super().run(
            token, 
            reconnect=reconnect, 
            *args, 
            **kwargs,
        )

    async def setup_hook(self) -> None:
        self.session = ClientSession()
        return await self.load_all_cogs()
    
    async def load_all_cogs(self, *, load_jishaku: bool = True) -> None:

        if load_jishaku:
            jishaku.Flags.NO_UNDERSCORE = True
            jishaku.Flags.NO_DM_TRACEBACK = True
            jishaku.Flags.HIDE = True

            await self.load_extension('jishaku')

        for ext in self.all_extensions:
            try:
                await self.load_extension(ext)
                self.logger.info(f'{ext} has been loaded')
            except Exception as e:
                self.logger.error(e)

    async def on_connect(self) -> None:
        self.logger.info('bot is connected')

    async def on_ready(self) -> None:
        self.logger.info('bot is ready')

    async def close(self) -> None:
        await self.session.close()
        return await super().close()

    async def get_context(self, message: discord.Message, *, cls: type[commands.Context] = BombContext) -> commands.Context | BombContext:
        return await super().get_context(message, cls=cls)

    async def post_mystbin(self, code: str, *, language: Optional[str] = None) -> str:
        MYSTBIN_URL = 'https://mystb.in/api/pastes'

        payload = MultipartWriter()
        content = payload.append(code)
        content.set_content_disposition('form-data', name='data')

        meta = {'index': 0}

        if language:
            meta['syntax'] = language

        content = payload.append_json(
            {'meta': [meta]}
        )

        content.set_content_disposition('form-data', name='meta')

        async with self.session.post(MYSTBIN_URL, data=payload) as r:
            if r.ok:
                data = await r.json()
                paste = 'https://mystb.in/' + data['pastes'][0]['id']
                return paste

    async def get_twemoji(self, emoji: str, *, svg: bool = True) -> Optional[bytes]:
        try:
            folder = ('72x72', 'svg')[svg]
            ext = ('png', 'svg')[svg]
            url = f'https://twemoji.maxcdn.com/v/latest/{folder}/{ord(emoji):x}.{ext}'

            async with self.session.get(url) as r:
                if r.ok:
                    byt = await r.read()
                    if svg:
                        with Image(
                            blob=byt, 
                            format='svg', 
                            width=500, 
                            height=500, 
                            background='none'
                        ) as asset:
                            return asset.make_blob('png')
                    else:
                        return byt
        except Exception:
            return None

    async def on_command_error(self, ctx: BombContext, error: Exception) -> Optional[discord.Message]:

        IGNORE_EXC = (
            commands.CommandNotFound,
            commands.NotOwner,
        )

        error = getattr(error, 'original', error)

        if isinstance(error, IGNORE_EXC):
            return

        elif isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(
                f'You are on cooldown! Try again after `{ceil(error.retry_after)}s`\n\n'
                f'`{ctx.command.qualified_name}` can only be used every `{round(error.cooldown.per)}s` per **{error.type.name}**'
            )

        elif isinstance(error, commands.MaxConcurrencyReached):
            return await ctx.send(f'`{ctx.command.qualified_name}` can only be used `{error.number}` times per **{error.per.name}**')

        if ctx.command:
            ctx.command.reset_cooldown(ctx)

        if isinstance(error, (ImageTooLarge, InvalidColor)):
            return await ctx.send(error.args[0])

        elif isinstance(error, commands.BadLiteralArgument):
            return await ctx.send(f"input value for `{error.param.name}` must be either ({'or'.join(error.literals)}) or nothing")

        elif isinstance(error, discord.HTTPException) and error.status == 415:
            return await ctx.send(f'Woops, the outputted image was too large :(')

        elif isinstance(error, commands.MemberNotFound):
            return await ctx.send(f'Member: `{error.argument}` could not be found')

        elif isinstance(error, commands.UserNotFound):
            return await ctx.send(f'User: `{error.argument}` could not be found')

        elif isinstance(error, commands.RangeError):
            return await ctx.send(f'value must be between `{error.minimum}` and `{error.maximum}`, not `{error.value}`')

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f'`{error.param.name}` is a required argument that is missing for the command `{ctx.command.qualified_name}`')

        elif isinstance(error, commands.ExtensionAlreadyLoaded):
            return await ctx.send(f'Extension `{error.name}` has already been loaded')
        
        elif isinstance(error, commands.ExtensionNotLoaded):
            return await ctx.send(f'Extension `{error.name}` has not been loaded yet')

        elif isinstance(error, commands.ExtensionNotFound):
            return await ctx.send(f'Extension `{error.name}` has not been found')

        elif isinstance(error, commands.NoEntryPointError):
            return await ctx.send(f'Extension `{error.name}` does not have a `setup` function')

        else:
            trace = traceback.format_exception(error.__class__, error, error.__traceback__)
            trace = f"```py\n{''.join(trace)}\n```"
            
            if len(trace) > 2000:
                trace = await ctx.bot.post_mystbin(trace)

            return await ctx.send(trace)