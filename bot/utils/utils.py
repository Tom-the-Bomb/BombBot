from __future__ import annotations

from typing import TYPE_CHECKING, Awaitable, Optional, Callable, TypeVar, ParamSpec, TypeAlias
import functools
import asyncio

import discord

__all__: tuple[str, ...] = (
    'to_thread',
    'truncate',
    'AuthorOnlyView',
    'Number',
    'num',
)

if TYPE_CHECKING:
    P = ParamSpec('P')
    T = TypeVar('T')

Number: TypeAlias = int | float

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

def truncate(content: str, limit: int = 2000) -> str:
    if len(content) > limit:
        return content[:1997] + '...'
    else:
        return content

class AuthorOnlyView(discord.ui.View):

    def __init__(self, author: discord.User, *, timeout: Optional[float] = None):
        super().__init__(timeout=timeout)
        self.author = author

    def disable_all(self) -> None:
        for button in self.children:
            if isinstance(button, discord.ui.Button):
                button.disabled = True

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
        self.has_timeout: bool = False

    async def on_timeout(self) -> None:
        self.has_timeout = True
        self.disable_all()
        return self.stop()

    @discord.ui.button(label='yes', style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.value = True
        self.disable_all()
        await interaction.response.edit_message(
            content=f'{self.author.mention} accepted!', 
            view=self,
            allowed_mentions=discord.AllowedMentions.none()
        )
        return self.stop()

    @discord.ui.button(label='no', style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.value = False
        self.disable_all()
        await interaction.response.edit_message(
            content=f'{self.author.mention} declined!', 
            view=self,
            allowed_mentions=discord.AllowedMentions.none()
        )
        return self.stop()