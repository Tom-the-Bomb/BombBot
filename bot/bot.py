from typing import Optional, TypedDict, Any
import os
import json
import logging
import traceback

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
    
    async def load_all_cogs(self, *, jishaku: bool = True) -> None:

        if jishaku:
            await self.load_extension('jishaku')

        for ext in os.listdir('./bot/ext'):
            if not ext.endswith(".py") or ext == '__init__.py':
                continue
            try:
                await self.load_extension('bot.ext.' + ext.removesuffix('.py'))
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

    async def on_command_error(self, ctx: BombContext, error: Exception) -> None:

        IGNORE_EXC = (
            commands.CommandNotFound,
            commands.NotOwner,
        )

        error = getattr(error, 'original', error)

        if isinstance(error, IGNORE_EXC):
            return
        elif isinstance(error, commands.CommandOnCooldown):
            return await ctx.send('you are on cooldown.')
        elif isinstance(error, commands.MaxConcurrencyReached):
            return await ctx.send('max concurrency reached for this command')
        else:
            trace = traceback.format_exception(type(error), error, error.__traceback__)
            trace = f"```py\n{''.join(trace)}\n```"
            
            if len(trace) > 2000:
                trace = await ctx.bot.post_mystbin(trace)

            return await ctx.send(trace)