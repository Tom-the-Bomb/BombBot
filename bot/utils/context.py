
from typing import Any, TYPE_CHECKING, Optional

import discord
from discord.ext import commands

from .helpers import ConfirmView, DeleteView
from .loading import Loading

if TYPE_CHECKING:
    from ..bot import BombBot

class BombContext(commands.Context['BombBot']):
    """Custom Context class for bombBot

    Overrides: send, reply
    New methods: confirm, loading
    """

    async def reply(self, content: Any = None, **kwargs: Any) -> discord.Message:
        """Overrides default reply method to set mention_author to False by default."""
        mention_author = kwargs.pop('mention_author', False)

        return await super().reply(
            content=content,
            mention_author=mention_author,
            **kwargs
        )

    async def send(self, content: Any = None, *, delete_button: bool = False, **kwargs: Any) -> discord.Message:
        """Custom send to incorporate a delete_button kwarg"""
        view: discord.ui.View
        has_del_view: bool = False

        if delete_button:
            if view := kwargs.get('view'):
                delview = DeleteView(self.author)
                view.add_item(delview.delete_button)

                has_del_view = True
            else:
                view = DeleteView(self.author)
                kwargs['view'] = view

        result = await super().send(content=content, **kwargs)

        if view := kwargs.get('view'):
            view.message = result

        if has_del_view:
            delview.message = result
        return result

    async def confirm(self, user: discord.Member, message: Optional[str] = None, *, timeout: Optional[float] = 1200) -> bool:
        """A helper method to send a confirmation view to `user` with `message`"""
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
        """A helper method returning a `Loading` context manager for image processing
        Similar to `Context.typing`
        """
        return Loading(self)