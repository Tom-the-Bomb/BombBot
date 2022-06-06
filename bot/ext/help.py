from __future__ import annotations

from typing import ClassVar, Optional, Mapping, TypeAlias, TYPE_CHECKING
from datetime import datetime as dt
import inspect

import discord
from discord.ext import commands

from ..utils.helpers import AuthorOnlyView
from ..utils.imaging import ImageConverter

if TYPE_CHECKING:
    from ..bot import BombBot
    from ..utils.context import BombContext

    HelpMapping: TypeAlias = Mapping[Optional[commands.Cog], list[commands.Command]]


class HelpSelect(discord.ui.Select['HelpView']):

    def __init__(self, mapping: HelpMapping) -> None:

        options = [
            discord.SelectOption(label=cog.qualified_name) for cog in 
            mapping.keys() if cog
        ]
        super().__init__(
            placeholder='Select a category to view',
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        help_menu = self.view.help_menu
        selected = self.values[0]

        if cog := help_menu.context.bot.get_cog(selected):
            embed = await help_menu.get_cog_embed(cog, self.view.commands_mapping)

            await interaction.response.edit_message(embed=embed)

class HelpView(AuthorOnlyView):

    def __init__(self, help_menu: BombHelp, mapping: HelpMapping, *, author: discord.User, timeout: float = None) -> None:
        super().__init__(author=author, timeout=timeout)

        self.help_menu = help_menu
        self.commands_mapping = mapping

        self.add_item(HelpSelect(self.commands_mapping))

    @discord.ui.button(label='Home', emoji='🏠', style=discord.ButtonStyle.gray, row=1)
    async def home_button(self, interaction: discord.Interaction, _) -> None:
        embed = await self.help_menu.get_home_embed(self.commands_mapping)
        await interaction.response.edit_message(embed=embed)

class BombHelp(commands.HelpCommand):
    context: BombContext
    _DOC_FORMATS_ENV: ClassVar[dict[str, str]] = {
        ':integer:': '[integer](https://en.wikipedia.org/wiki/Integer)',
        ':decimal:': '[decimal](https://en.wikipedia.org/wiki/Decimal)',
        ':css:': '[css syntax](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value)'
    }

    def get_base_embed(self) -> discord.Embed:
        ctx = self.context
        embed = discord.Embed(
            description='',
            timestamp=dt.utcnow(),
            color=ctx.bot.EMBED_COLOR,
        )
        embed.set_thumbnail(url=ctx.bot.user.display_avatar.url)
        embed.set_author(
            name=ctx.author.display_name, 
            icon_url=ctx.author.display_avatar.url,
        )
        return embed

    async def get_home_embed(self, mapping: HelpMapping) -> discord.Embed:
        ctx = self.context
        embed = self.get_base_embed()
        embed.description = (
            f'{ctx.bot.description}\n\n'
            f'Use `{ctx.clean_prefix}{self.invoked_with} <command>` for more information on a specific command.\n\n'
        )
        for cog, cmds in mapping.items():
            cmds = await self.filter_commands(cmds)

            if cog and cmds:
                embed.description += f'**{cog.qualified_name}**\n{cog.description}\n\n'
        return embed

    async def get_cog_embed(self, cog: commands.Cog, mapping: HelpMapping) -> discord.Embed:
        embed = self.get_base_embed()
        embed.title = cog.qualified_name

        cmds = await self.filter_commands(mapping.get(cog), sort=True)
        description = '` | `'.join([cmd.qualified_name for cmd in cmds]) or 'none'
        embed.description = f'{cog.description}\n\n`{description}`'

        return embed

    def _format_param(self, name: str, param: commands.Parameter) -> str:
        annotation = (
            'A valid `image` source, optional\n(by default the author\'s avatar)' if param.converter in (Optional[ImageConverter], ImageConverter)
            else 'see "Options" below' if name == 'options'
            else getattr(param.converter, '__name__', param.converter)
        )

        string = f'• `{name}` {annotation}'
        if param.default != inspect._empty:
            string += f' (by default {param.default}'
        return string

    def get_param_doc(self, params: dict[str, commands.Parameter]) -> str:
        return '\n'.join(
            self._format_param(name, param) for name, param in params.items()
        ) or '-'

    def get_flag_doc(self, command: commands.Command) -> str:
        if flags := command.clean_params.get('options'):
            if issubclass(converter := flags.converter, commands.FlagConverter):
                doc = inspect.getdoc(converter).strip() or '-'

                for key, value in self._DOC_FORMATS_ENV.items():
                    doc = doc.replace(key, value)
                return doc

    def get_command_embed(self, command: commands.Command) -> discord.Embed:
        signature = self.get_command_signature(command)
        aliases = '` `'.join(command.aliases) or 'none'

        embed = self.get_base_embed()
        embed.title = command.qualified_name
        embed.description = f'```ps\n{signature}\n```\n{command.help}\n\n\u200b'
        embed.add_field(name='Aliases:', value=f'`{aliases}`', inline=False)

        if params := command.clean_params:
            embed.add_field(name='Parameters', value=self.get_param_doc(params))
        
        if flags := self.get_flag_doc(command):
            embed.add_field(name='Options', value=flags or '-', inline=False)

        if isinstance(command, commands.Group):
            subcommands = '`\n`'.join(cmd.qualified_name for cmd in command.commands) or 'none'
            embed.add_field(name='Subcommands', value=f'`{subcommands}`')
        return embed

    async def send_bot_help(self, mapping: HelpMapping) -> None:
        embed = await self.get_home_embed(mapping)

        channel = self.get_destination()
        view = HelpView(self, mapping, author=self.context.author)

        await channel.send(embed=embed, view=view)

    async def send_command_help(self, command: commands.Command) -> None:
        embed = self.get_command_embed(command)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_group_help(self, group: commands.Group) -> None:
        return await self.send_command_help(group)

    async def send_cog_help(self, cog: commands.Cog) -> None:
        mapping = {cog: cog.get_commands()}
        embed = await self.get_cog_embed(cog, mapping)

        channel = self.get_destination()
        await channel.send(embed=embed)


class Help(commands.Cog):
    """Help Command, that's quite about it"""
    def __init__(self, bot: BombBot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.bot.help_command = BombHelp()
        self.bot.help_command.cog = self

    async def cog_unload(self) -> None:
        self.bot.help_command = None

async def setup(bot: BombBot) -> None:
    await bot.add_cog(Help(bot))