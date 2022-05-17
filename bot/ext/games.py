from typing import Optional, Literal

import discord_games as games
from discord_games import button_games

import discord
from discord.ext import commands

from ..utils.context import BombContext
from ..bot import BombBot


class Games(commands.Cog):

    def __init__(self, bot: BombBot) -> None:
        self.bot = bot
        self.twenty_48_emojis: dict[str, str] = {
            '0': '<:_0:972626053078069298>',
            '2': '<:_2:972626055087136789>',
            '4': '<:_4:972626057398210590>',
            '8': '<:_8:972626059923185724>',
            '16': '<:_16:972626061923864586>',
            '32': '<:_32:972626074951368714>',
            '64': '<:_64:972626077337919608>',
            '128': '<:_128:972626079388926063>',
            '256': '<:_256:972626081251205120>',
            '512': '<:_512:972626083180576838>',
            '1024': '<:_1024:972626096820473917>',
            '2048': '<:_2048:972626098972164137>',
            '4096': '<:_4096:972626101828460664>',
            '8192': '<:_8192:972626103854309477>',
        }

        self.is_in_battleship: set[discord.Member] = set()

    @commands.command(name='connect4', aliases=['c4'])
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def connect4(self, ctx: BombContext, opponent: discord.Member) -> None:
        if await ctx.confirm(opponent, f'{opponent.mention} do you accept to play connect 4?'):
            game = games.ConnectFour(
                red=ctx.author,         
                blue=opponent,             
            )
            await game.start(ctx)
    
    @commands.command(name='tictactoe', aliases=['ttt'])
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def tictactoe(self, ctx: BombContext, opponent: discord.Member) -> None:
        if await ctx.confirm(opponent, f'{opponent.mention} do you accept to play tictactoe?'):
            game = button_games.BetaTictactoe(
                cross=ctx.author,         
                circle=opponent,             
            )
            await game.start(ctx, timeout=600)

    @commands.command(name='hangman')
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def hangman(self, ctx: BombContext):
        game = button_games.BetaHangman()
        await game.start(ctx, timeout=600)

    @commands.command(name='chess')
    @commands.max_concurrency(2, commands.BucketType.channel)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def chess(self, ctx: BombContext, opponent: discord.Member) -> None:
        if await ctx.confirm(opponent, f'{opponent.mention} do you accept to play chess?'):
            game = button_games.BetaChess(
                white=ctx.author,         
                black=opponent,             
            )
            await game.start(ctx, timeout=1000)

    @commands.command(name='twenty48', aliases=['2048'])
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def twenty48(self, ctx: BombContext, render_image: Optional[Literal['-r']]) -> None:
        game = button_games.BetaTwenty48(self.twenty_48_emojis, render_image=bool(render_image))
        await game.start(ctx, timeout=600, delete_button=True)

    @commands.command(name='akinator', aliases=['aki', 'guesscharacter', 'characterguess', 'guess'])
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def akinator(self, ctx: BombContext) -> None:
        async with ctx.typing():
            game = button_games.BetaAkinator()
            await game.start(
                ctx=ctx, 
                timeout=300, 
                back_button=True, 
                delete_button=True,
            )

    @commands.command(name='typerace', aliases=['tr'])
    @commands.max_concurrency(2, commands.BucketType.channel)
    @commands.cooldown(1, 20, commands.BucketType.channel)
    async def typerace(self, ctx: BombContext) -> None:
        game = games.TypeRacer()
        await game.start(ctx)
        
    @commands.command(name='battleship', aliases=['bs'])
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def battleship(self, ctx: BombContext, opponent: discord.Member) -> None:
        no_mentions = discord.AllowedMentions.none()
        if ctx.author in self.is_in_battleship:
            return await ctx.send(f'{ctx.author.mention} is already in a game!', allowed_mentions=no_mentions)

        if opponent in self.is_in_battleship:
            return await ctx.send(f'{opponent.mention} is already in a game!', allowed_mentions=no_mentions)

        if await ctx.confirm(opponent, f'{opponent.mention} do you accept to play battleship?'):
            self.is_in_battleship.add(ctx.author)
            self.is_in_battleship.add(opponent)

            game = button_games.BetaBattleShip(ctx.author, opponent)
            await game.start(ctx, timeout=1800)

            self.is_in_battleship.remove(ctx.author)
            self.is_in_battleship.remove(opponent)

    @commands.command(name='wordle', aliases=['wd'])
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def wordle(self, ctx: BombContext) -> None:
        game = button_games.BetaWordle()
        await game.start(ctx)

    @commands.command(name='memory-game', aliases=['mem'])
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def memory_game(self, ctx: BombContext) -> None:
        game = button_games.MemoryGame()
        await game.start(ctx, timeout=300)

    @commands.command(name='rockpaperscissors', aliases=['rps'])
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def rps(self, ctx: BombContext, member: Optional[discord.Member] = None) -> None:
        game = button_games.BetaRockPaperScissors(member)
        await game.start(ctx, timeout=120)

    @commands.command(name='reaction', aliases=['react'])
    @commands.max_concurrency(1, commands.BucketType.channel)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def reaction(self, ctx: BombContext) -> None:
        game = button_games.BetaReactionGame()
        await game.start(ctx, timeout=60)

    @commands.command(name='country', aliases=['cg'])
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def country(
        self, 
        ctx: BombContext, 
        guess_flags: Optional[Literal['-f']], 
        light_mode: Optional[Literal['-l']],
        blur: Optional[Literal['-b']],
    ) -> None:
        game = button_games.BetaCountryGuesser(
            is_flags=bool(guess_flags),
            hard_mode=bool(blur),
            light_mode=bool(light_mode),
        )
        await game.start(ctx, timeout=1200)

    @commands.command(name='slider', aliases=['slide', 'slidepuzzle', 'numberslider'])
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def number_slider(self, ctx: BombContext, *, count: commands.Range[int, 1, 5] = 4) -> None:
        game = button_games.NumberSlider(count)
        await game.start(ctx, timeout=600)

    @commands.command(name='lightsout', aliases=['lo'])
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def lights_out(self, ctx: BombContext, *, count: commands.Range[int, 1, 5] = 4) -> None:
        game = button_games.LightsOut(count)
        await game.start(ctx, timeout=600)

    @commands.command(name='boggle', aliases=['bg'])
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def boggle(self, ctx: BombContext) -> None:
        game = button_games.Boggle()
        await game.start(ctx, timeout=600)

async def setup(bot: BombBot) -> None:
    await bot.add_cog(Games(bot))