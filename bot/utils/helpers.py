from __future__ import annotations

from typing import (
    TYPE_CHECKING, 
    Awaitable, 
    Optional, 
    Callable, 
    TypeVar, 
    ParamSpec, 
    TypeAlias,
    ClassVar,
)
import functools
import asyncio
import re
import os

import discord

__all__: tuple[str, ...] = (
    'chunk',
    'to_thread',
    'truncate',
    'AuthorOnlyView',
    'Number',
    'num',
    'Regexes',
)

if TYPE_CHECKING:
    P = ParamSpec('P')
    T = TypeVar('T')

Number: TypeAlias = int | float

def get_asset(file: str) -> str:
    return os.path.join('C:/Users/Tom the Bomb/BombBot/assets/', file)
    
def chunk(iterable: list[int], *, count: int) -> list[list[int]]:
    return [iterable[i:i + count] for i in range(0, len(iterable), count)]

def num(n: str) -> Number:
    n = float(n)
    if n.is_integer():
        n = int(n)
    return n

def to_thread(func: Callable[P, T]) -> Callable[P, Awaitable[T]]:

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Awaitable[T]:
        return asyncio.to_thread(func, *args, **kwargs)

    return wrapper

def truncate(content: str, limit: int = 2000, *, placeholder: str = '...') -> str:
    if len(content) > limit:
        return content[:limit - len(placeholder)] + placeholder
    else:
        return content

class Regexes:
    TENOR_PAGE_REGEX: ClassVar[re.Pattern] = re.compile(r'https?://(www\.)?tenor\.com/view/\S+')
    TENOR_GIF_REGEX: ClassVar[re.Pattern] = re.compile(r'https?://(www\.)?c\.tenor\.com/\S+/\S+\.gif')
    CUSTOM_EMOJI_REGEX: ClassVar[re.Pattern] = re.compile(r'<(a)?:([a-zA-Z0-9_]{2,32}):([0-9]{18,22})>')

class AuthorOnlyView(discord.ui.View):

    def __init__(self, author: discord.User, *, timeout: Optional[float] = None):
        super().__init__(timeout=timeout)

        self.message: Optional[discord.Message] = None
        self.author = author

    def disable_all(self) -> None:
        for button in self.children:
            if isinstance(button, discord.ui.Button):
                button.disabled = True

    async def on_timeout(self) -> None:
        self.disable_all()
        if self.message:
            await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message(f'This interaction can only be used by {self.author.mention}', ephemeral=True)
            return False
        else:
            return True

class ConfirmView(AuthorOnlyView):

    def __init__(self, user: discord.Member, *, timeout: Optional[float] = None) -> None:
        super().__init__(user, timeout=timeout)

        self.value: bool = False

    @discord.ui.button(label='yes', style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, _) -> None:
        self.value = True
        self.disable_all()
        await interaction.response.edit_message(
            content=f'{self.author.mention} accepted!', 
            view=self,
            allowed_mentions=discord.AllowedMentions.none()
        )
        return self.stop()

    @discord.ui.button(label='no', style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, _) -> None:
        self.value = False
        self.disable_all()
        await interaction.response.edit_message(
            content=f'{self.author.mention} declined!', 
            view=self,
            allowed_mentions=discord.AllowedMentions.none()
        )
        return self.stop()


class ConfirmDeletionView(AuthorOnlyView):

    @discord.ui.button(label='yes', style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, _) -> None:
        self.disable_all()
        try:
            if msg := self.message:
                await msg.delete()
        except discord.Forbidden:
            await interaction.response.send_message('Sorry, I cannot delete messages within a DM', ephemeral=True)
        else:
            await interaction.response.edit_message(content='Deleted!', view=self)

    @discord.ui.button(label='no', style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, _) -> None:
        self.disable_all()
        await interaction.response.edit_message(content='Ok, aborting', view=self)

class DeleteView(AuthorOnlyView):

    @discord.ui.button(emoji='🗑️', style=discord.ButtonStyle.red)
    async def delete_button(self, interaction: discord.Interaction, _) -> None:
        view = ConfirmDeletionView(self.author)
        view.message = self.message

        await interaction.response.send_message(
            content='Are you sure you want to delete this?', 
            view=view,
            ephemeral=True,
        )