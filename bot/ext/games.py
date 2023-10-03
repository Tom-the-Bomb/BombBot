from typing import Optional, Literal

import discord_games as games
from discord_games import button_games

import discord
from discord.ext import commands

from ..utils.context import BombContext
from ..bot import BombBot


class Games(commands.Cog):
    """Several classic games"""

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

    @commands.command(name='connect4', aliases=('c4',))
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def connect4(self, ctx: BombContext, opponent: discord.Member) -> None:
        """Starts a connect-4 game with the provided `opponent`"""
        if await ctx.confirm(opponent, f'{opponent.mention} do you accept to play connect 4?'):
            game = games.ConnectFour(
                red=ctx.author,
                blue=opponent,
            )
            await game.start(ctx)

    @commands.command(name='tictactoe', aliases=('ttt',))
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def tictactoe(self, ctx: BombContext, opponent: discord.Member) -> None:
        """Starts a tictactoe game with the provided `opponent`"""
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
        """Starts a hangman game (singleplayer)"""
        game = button_games.BetaHangman()
        await game.start(ctx, timeout=600)

    @commands.command(name='chess')
    @commands.max_concurrency(2, commands.BucketType.channel)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def chess(self, ctx: BombContext, opponent: discord.Member) -> None:
        """Starts a chess game with the provided `opponent`

        💡 Moves are made using a modal, with 2 textboxes (in `uci` format):
        1. (From) Enter the from coordinate. (Ex: `a2`)
        2. (To) Enter the coordinate to move to. (Ex: `a4`)
        """
        if await ctx.confirm(opponent, f'{opponent.mention} do you accept to play chess?'):
            game = button_games.BetaChess(
                white=ctx.author,
                black=opponent,
            )
            await game.start(ctx, timeout=1000)

    @commands.command(name='twenty48', aliases=('2048',))
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def twenty48(self, ctx: BombContext, render_image: Optional[Literal['-r']]) -> None:
        """Starts a 2048 game (singleplayer)

        - Specify the optional `-r` option to choose to render the board as an *image*
        """
        game = button_games.BetaTwenty48(self.twenty_48_emojis, render_image=bool(render_image))
        await game.start(ctx, timeout=600, delete_button=True)

    @commands.command(name='akinator', aliases=('aki', 'guesscharacter', 'characterguess', 'guess'))
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def akinator(self, ctx: BombContext) -> None:
        """Starts an Akinator Game"""
        async with ctx.typing():
            game = button_games.BetaAkinator()
            await game.start(
                ctx=ctx,
                timeout=300,
                back_button=True,
                delete_button=True,
            )

    @commands.command(name='typerace', aliases=('tr',))
    @commands.max_concurrency(2, commands.BucketType.channel)
    @commands.cooldown(1, 20, commands.BucketType.channel)
    async def typerace(self, ctx: BombContext) -> None:
        """Starts a multiplayer typerace game in the channel
        the game ends upon the first 3 responses above 90% accuracy
        """
        game = games.TypeRacer()
        await game.start(ctx)

    @commands.command(name='battleship', aliases=('bs',))
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def battleship(
        self,
        ctx: BombContext,
        opponent: discord.Member,
        choose_pos: Optional[Literal['-c']],
    ) -> None:
        """Starts a battleship game with the provided `opponent`
        occurs in respective DMs

        - Specify the optional `-c` option to allow the *users* to (custom) choose their ship placements
        """
        no_mentions = discord.AllowedMentions.none()
        if ctx.author in self.is_in_battleship:
            return await ctx.send(f'{ctx.author.mention} is already in a game!', allowed_mentions=no_mentions)

        if opponent in self.is_in_battleship:
            return await ctx.send(f'{opponent.mention} is already in a game!', allowed_mentions=no_mentions)

        if await ctx.confirm(opponent, f'{opponent.mention} do you accept to play battleship?'):
            self.is_in_battleship.add(ctx.author)
            self.is_in_battleship.add(opponent)

            game = button_games.BetaBattleShip(ctx.author, opponent, random=not bool(choose_pos))
            await game.start(ctx, timeout=1800)

            self.is_in_battleship.remove(ctx.author)
            self.is_in_battleship.remove(opponent)

    @commands.command(name='wordle', aliases=('wd',))
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def wordle(self, ctx: BombContext) -> None:
        """Starts a wordle game (singleplayer)"""
        game = button_games.BetaWordle()
        await game.start(ctx)

    @commands.command(name='memory-game', aliases=('mem',))
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def memory_game(self, ctx: BombContext) -> None:
        """Starts a memory game (singleplayer)
        where you have to match pairs of "items" to each other
        """
        game = button_games.MemoryGame()
        await game.start(ctx, timeout=300)

    @commands.command(name='rockpaperscissors', aliases=('rps',))
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def rps(self, ctx: BombContext, opponent: Optional[discord.Member] = None) -> None:
        """Starts a game of Rock paper scissors.
        If `opponent` is not specified, it defaults to playing against the bot.
        """
        game = button_games.BetaRockPaperScissors(opponent)
        await game.start(ctx, timeout=120)

    @commands.command(name='reaction', aliases=('react',))
    @commands.max_concurrency(1, commands.BucketType.channel)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def reaction(self, ctx: BombContext) -> None:
        """Starts a reaction speed test game (multiplayer)
        Whoever clicks first, wins!
        """
        game = button_games.BetaReactionGame()
        await game.start(ctx, timeout=60)

    @commands.command(name='country', aliases=('cg',))
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def country(
        self,
        ctx: BombContext,
        guess_flags: Optional[Literal['-f']],
        light_mode: Optional[Literal['-l']],
        blur: Optional[Literal['-b']],
    ) -> None:
        """Starts a country guessing game (singleplayer)

        - Specify the optional `-f` option to *guess flags* instead
        - Specify the optional `-l` option if you are on discord light mode (black assets)
        - Specify the optional `-b` option to blur the image (harder)
        """
        game = button_games.BetaCountryGuesser(
            is_flags=bool(guess_flags),
            hard_mode=bool(blur),
            light_mode=bool(light_mode),
        )
        await game.start(ctx, timeout=1200)

    @commands.command(name='slider', aliases=('slide', 'slidepuzzle', 'numberslider'))
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def number_slider(self, ctx: BombContext, *, count: commands.Range[int, 1, 5] = 4) -> None:
        """Starts a number slider game (singleplayer)
        Slide the numbers back into ascending order!
        """
        game = button_games.NumberSlider(count)
        await game.start(ctx, timeout=600)

    @commands.command(name='lightsout', aliases=('lo',))
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def lights_out(self, ctx: BombContext, *, count: commands.Range[int, 1, 5] = 4) -> None:
        """
        Starts a Lights-out game (singleplayer)
        Each click will toggle inverse itself and all the 4 tiles adjacent to itself
        Turn off all the lights!
        """
        game = button_games.LightsOut(count)
        await game.start(ctx, timeout=600)

    @commands.command(name='boggle', aliases=('bg',))
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def boggle(self, ctx: BombContext) -> None:
        """Starts a game of boggle (singleplayer)"""
        game = button_games.Boggle()
        await game.start(ctx, timeout=600)

    @commands.command(name='verbalmem', aliases=('verbalmemory',))
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def verbalmem(self, ctx: BombContext, lives: int = 3) -> None:
        """Starts a verbal memory game (singleplayer)"""
        game = button_games.VerbalMemory()
        await game.start(ctx, lives=lives, timeout=600)

    @commands.command(name='chimptest', aliases=('chimp',))
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def chimptest(self, ctx: BombContext, *, count: commands.Range[int, 1, 25] = 9) -> None:
        """Starts a chimp test game (singleplayer)"""
        game = button_games.ChimpTest(count)
        await game.start(ctx, timeout=600)

    @commands.command(name='numbermem', aliases=('nummem',))
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def numbermem(self, ctx: BombContext) -> None:
        """Starts a number memory game (singleplayer)"""
        game = button_games.NumberMemory()
        await game.start(ctx, timeout=600)

async def setup(bot: BombBot) -> None:
    await bot.add_cog(Games(bot))