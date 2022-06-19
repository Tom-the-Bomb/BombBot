from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    TypedDict,
    Optional,
    ClassVar,
    Any,
)
import pathlib
import json
import logging
import traceback
from math import ceil
from inspect import getdoc
from datetime import datetime

import jishaku
import discord
from discord.ext import commands
from aiohttp import MultipartWriter, ClientSession

from .utils.context import BombContext
from .utils.imaging import BaseImageException, svg_to_png

if TYPE_CHECKING:

    class Config(TypedDict):
        TOKEN: str
        PREFIXES: list[str]

    class CodeData(TypedDict):
        classes: int
        funcs: int
        coros: int
        files: int
        lines: int


class BombBot(commands.Bot):
    """A multipurpose discord bot featuring numerous games and image processing command among many others
    """
    EMBED_COLOR: ClassVar[int] = 0x2F3136

    def __init__(self, **options: Any) -> None:

        self.session: Optional[ClientSession] = None
        self.code_stats: CodeData = {
            'classes': 0,
            'funcs': 0,
            'coros': 0,
            'files': 0,
            'lines': 0,
        }

        self.config: Config = self.load_config()
        self.default_prefixes: list[str] = self.config['PREFIXES']
        self.token: str = self.config['TOKEN']

        self.setup_logging()
        self.cache_code_stats()

        intents = discord.Intents.all()

        self.launch_time: datetime = datetime.utcnow()

        super().__init__(
            command_prefix=commands.when_mentioned_or(*self.default_prefixes),
            description=getdoc(self),
            intents=intents,
            strip_after_prefix=True,
            case_insensitive=True,
            status=discord.Status.idle,
            activity=discord.Game('beep boop'),
            **options,
        )

    @discord.utils.cached_property
    def invite_url(self) -> str:
        return discord.utils.oauth_url(
            client_id=self.user.id,
            permissions=discord.Permissions(416313375937),
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

    def get_uptime(self) -> tuple[int, int, int, int]:
        delta = (datetime.utcnow() - self.launch_time)
        delta = round(delta.total_seconds())

        days, left = divmod(delta, 86400)
        hours, left = divmod(left, 3600)
        mins, secs = divmod(left, 60)
        return days, hours, mins, secs

    def cache_code_stats(self) -> None:
        self.code_stats = {
            'classes': 0,
            'funcs': 0,
            'coros': 0,
            'files': 0,
            'lines': 0,
        }

        for file in pathlib.Path('./').rglob('*.py'):
            with file.open(errors='replace') as fp:

                for line in fp.readlines():
                    line = line.strip()
                    if line.startswith('class '):
                        self.code_stats['classes'] += 1
                    if line.startswith('def '):
                        self.code_stats['funcs'] += 1
                    if line.startswith('async def '):
                        self.code_stats['coros'] += 1

                    self.code_stats['lines'] += 1
                self.code_stats['files'] += 1

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

            await self.load_extension('jishaku', recache_stats=False)

        for ext in self.all_extensions:
            try:
                await self.load_extension(ext, recache_stats=False)
                self.logger.info(f'{ext} has been loaded')
            except Exception as e:
                self.logger.error(e)

    async def load_extension(
        self,
        name: str,
        *,
        package: Optional[str] = None,
        recache_stats: bool = True,
    ) -> None:
        if recache_stats:
            self.cache_code_stats()
        return await super().load_extension(name, package=package)

    async def reload_extension(
        self,
        name: str,
        *,
        package: Optional[str] = None,
        recache_stats: bool = True,
    ) -> None:
        if recache_stats:
            self.cache_code_stats()
        return await super().reload_extension(name, package=package)

    async def on_connect(self) -> None:
        self.logger.info('bot is connected')

    async def on_ready(self) -> None:
        self.logger.info('bot is ready')

    async def close(self) -> None:
        if session := self.session:
            await session.close()
        return await super().close()

    async def get_context(self, message: discord.Message, *, cls: type[commands.Context] = BombContext) -> commands.Context | BombContext:
        return await super().get_context(message, cls=cls)

    async def post_mystbin(self, code: str, *, language: Optional[str] = None) -> Optional[str]:
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

    async def get_default_emoji(self, emoji: str, *, svg: bool = True) -> Optional[bytes]:
        try:
            if len(emoji) > 1:
                svg = False
                url = f'https://emojicdn.elk.sh/{emoji}?style=twitter'
            else:
                folder = ('72x72', 'svg')[svg]
                ext = ('png', 'svg')[svg]
                url = f'https://twemoji.maxcdn.com/v/latest/{folder}/{ord(emoji):x}.{ext}'

            async with self.session.get(url) as r:
                if r.ok:
                    byt = await r.read()
                    if svg:
                        return await svg_to_png(byt)
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

        if isinstance(error, BaseImageException):
            return await ctx.send(error.message)

        elif isinstance(error, commands.BadLiteralArgument):
            return await ctx.send(f"input value for `{error.param.name}` must be either ({'or'.join(error.literals)}) or nothing")

        elif isinstance(error, discord.HTTPException) and error.status == 413:
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

        elif isinstance(error, commands.BadArgument):
            return await ctx.send(str(error))

        else:
            trace = traceback.format_exception(error.__class__, error, error.__traceback__)
            trace = f"```py\n{''.join(trace)}\n```"

            if len(trace) > 2000:
                trace = await ctx.bot.post_mystbin(trace)

            return await ctx.send(trace)