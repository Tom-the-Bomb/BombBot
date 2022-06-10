from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import cv2
import discord

from ..helpers import AuthorOnlyView
from ..loading import Loading
from .image import pil_image, to_array

if TYPE_CHECKING:
    from numpy import ndarray
    from ..context import BombContext

__all__: tuple[str, ...] = (
    'apply_color_map',
    'ColorMapSelect',
    'COlorMapView',
)

@pil_image()
@to_array()
def apply_color_map(_, img: ndarray, *, colormap: str) -> ndarray:
    return cv2.applyColorMap(
        src=img, 
        colormap=getattr(cv2, colormap, 0)
    )

def _humanize_colormap(colormap: str) -> str:
    colormap = colormap.removeprefix('COLORMAP_')
    return colormap.capitalize().replace('_', '-')

class ColorMapSelect(discord.ui.Select['ColorMapView']):

    def __init__(
        self, 
        context: BombContext,
        argument: Optional[bytes], 
        colormaps: list[str]
    ) -> None:
        
        self.context = context
        self.argument = argument

        options = [
            discord.SelectOption(
                label=_humanize_colormap(colormap),
                value=colormap,
            )
            for colormap in colormaps
        ]
        super().__init__(
            placeholder='Select a colormap to apply',
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        colormap = self.values[0]

        async with self.context.typing():
            embed = discord.Embed(
                description=Loading.MESSAGE, 
                color=self.context.bot.EMBED_COLOR,
            )
            await interaction.response.edit_message(embed=embed, attachments=[])

            output_file: discord.File = await apply_color_map(
                self.context, 
                self.argument, 
                colormap=colormap,
            )

            embed.description = f'Applied `{_humanize_colormap(colormap)}` to provided image.'
            embed.set_image(url=f'attachment://{output_file.filename}')

            await interaction.edit_original_message(
                embed=embed, 
                attachments=[output_file],
            )

class ColorMapView(AuthorOnlyView):

    def __init__(
        self, 
        context: BombContext, 
        argument: Optional[bytes], 
        *, 
        timeout: Optional[float] = None,
    ) -> None:

        super().__init__(author=context.author, timeout=timeout)

        colormaps = [attr for attr in dir(cv2) if attr.startswith('COLORMAP_')][:25]
        self.add_item(ColorMapSelect(context, argument, colormaps))