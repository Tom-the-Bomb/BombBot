
from typing import Any, TYPE_CHECKING, Optional

import discord
from discord.ext import commands

from .helpers import ConfirmView, DeleteView
from .loading import Loading

if TYPE_CHECKING:
    from ..bot import BombBot

class BombContext(commands.Context['BombBot']):

    async def reply(self, content: Any = None, **kwargs: Any) -> discord.Message:
        mention_author = kwargs.pop('mention_author', False)
        
        return await super().reply(
            content=content, 
            mention_author=mention_author, 
            **kwargs
        )

    async def send(self, content: Any = None, **kwargs: Any) -> discord.Message:
        if kwargs.pop('delete_button', False):
            if view := kwargs.get('view'):
                view.add_item(DeleteView.delete_button)
            else:
                view = DeleteView(self.author)
                kwargs['view'] = view

        result = await super().send(content=content, **kwargs)
    
        if view := kwargs.get('view'):
            view.message = result
        return result

    async def confirm(self, user: discord.Member, message: Optional[str] = None, *, timeout: Optional[float] = 1200) -> bool:
        message = message or f'{user.mention} do you accept?'

        view = ConfirmView(user, timeout=timeout)
        view.message = msg = await self.send(content=message, view=view)

        if await view.wait():
            await msg.edit(
                content=f'Looks like {user.mention} did not respond.', 
                allowed_mentions=discord.AllowedMentions.none()
            )
            return False
        else:
            return view.value

    def loading(self) -> Loading:
        return Loading(self)