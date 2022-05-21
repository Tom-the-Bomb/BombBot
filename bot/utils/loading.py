from __future__ import annotations

from typing import TYPE_CHECKING, Optional, ClassVar

from discord.context_managers import Typing

if TYPE_CHECKING:
    from types import TracebackType
    from discord import Message

__all__: tuple[str, ...] = ('Loading',)

class Loading(Typing):
    MESSAGE: ClassVar[str] = '<a:rooHacker:977335964412305458> | Processing Image... Please wait'

    async def __aenter__(self) -> None:
        self._message: Message = await self.messageable.send(self.MESSAGE)
        return await super().__aenter__()

    async def __aexit__(
        self, 
        exc_type: Optional[type[BaseException]], 
        exc_val: Optional[BaseException], 
        exc_tb: Optional[TracebackType],
    ) -> None:

        await self._message.delete()
        return await super().__aexit__(exc_type, exc_val, exc_tb)