from __future__ import annotations

from typing import TYPE_CHECKING
from io import BytesIO

import matplotlib
matplotlib.use('agg')

from matplotlib import pyplot as plt
plt.style.use(('bmh', 'ggplot'))

import discord

from ..helpers import to_thread

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

__all__: tuple[str, ...] = (
    'boxplot',
)


@to_thread
def boxplot(_, data: list[float], *, fill_boxes: bool = True) -> discord.File:
    fig: Figure = plt.figure()
    ax: Axes = fig.add_subplot()
    ax.set_title('Box & Whisker Plot', pad=15)

    out = ax.boxplot(
        x=data,
        vert=False,
        showmeans=True,
        patch_artist=fill_boxes,
    )

    for cap in out.get('caps', ()):
        cap.set(color='#8B008B', linewidth=2)

    for whisk in  out.get('whiskers', ()):
        whisk.set(color='#5043a9', linewidth=2)

    for box in  out.get('boxes', ()):
        box.set(color='#71525b', linewidth=2)

    for median in  out.get('medians', ()):
        median.set(color='#b54d6a', linewidth=2)
    
    buffer = BytesIO()
    plt.savefig(buffer)
    plt.close()
    buffer.seek(0)
    return discord.File(buffer, 'graph.png')