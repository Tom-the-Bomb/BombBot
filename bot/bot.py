from distutils.command.build_ext import extension_name_re
from os import extsep
from typing import Optional, TypedDict, Any
import pathlib
import json
import logging
import traceback
from math import ceil
from io import BytesIO

import jishaku
import discord
from discord.ext import commands
from aiohttp import MultipartWriter, ClientSession

from .utils.context import BombContext

class Config(TypedDict):
    TOKEN: str
    PREFIXES: list[str]

class BombBot(commands.Bot):

    def __init__(self, **options: Any) -> None:

        self.session: Optional[ClientSession] = None

        self.config: Config = self.load_config()
        self.default_prefixes: list[str] = self.config['PREFIXES']
        self.token: str = self.config['TOKEN']

        self.setup_logging()

        intents = discord.Intents.all()
        
        super().__init__(
            command_prefix=commands.when_mentioned_or(*self.default_prefixes), 
            description='BombBot rewrite',
            intents=intents,
            case_insensitive=True, 
            status=discord.Status.idle,
            activity=discord.Game('beep boop'),
            **options,
        )

    @property
    def all_extensions(self) -> list[str]:
        exts = pathlib.Path('./bot/ext').glob('**/[!_]*.py')
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
            except Exception as e:
                self.logger.error(e)

    async def on_connect(self) -> None:
        self.logger.info('bot is connected')

    async def on_ready(self) -> None:
        self.logger.info('bot is ready')

    async def close(self) -> None:
        await self.session.close()
        return await super().close()

    async def get_context(self, message: discord.Message, *, cls: type[commands.Context] = BombContext) -> commands.Context:
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

        content.set_content_disposition("form-data", name='meta')

        async with self.session.post(MYSTBIN_URL, data=payload) as r:
            if r.ok:
                data = await r.json()
                paste = 'https://mystb.in/' + data['pastes'][0]['id']
                return paste

    async def get_twemoji(self, emoji: str) -> Optional[bytes]:
        try:
            url = f'https://twemoji.maxcdn.com/v/latest/72x72/{ord(emoji):x}.png'

            async with self.session.get(url) as r:
                if r.ok:
                    return await r.read()
        except Exception:
            return None

    async def on_command_error(self, ctx: BombContext, error: Exception) -> Optional[discord.Message]:

        IGNORE_EXC = (
            commands.CommandNotFound,
            commands.NotOwner,
        )

        error = getattr(error, '__cause__', error)

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

        if isinstance(error, commands.BadLiteralArgument):
            return await ctx.send(f'input value for `{error.param.name}` must be either `{error.literals[0]}` or nothing')

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