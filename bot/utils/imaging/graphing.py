from __future__ import annotations

import re
from typing import TYPE_CHECKING
from io import BytesIO
from statistics import (
    mean,
    mode,
    quantiles,
)

import numpy as np
import matplotlib
matplotlib.use('agg')

from matplotlib import pyplot as plt
plt.style.use(('bmh', 'ggplot'))

import discord
from Equation import Expression

from ..helpers import to_thread

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

__all__: tuple[str, ...] = (
    'boxplot',
    'plotfn',
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

    _min, _max = min(data), max(data)
    ax.text(_min, 1.4, f'Min: {_min}')
    ax.text(_min, 1.34, f'Max: {_max}')
    ax.text(_min, 1.28, f'Range: {_max - _min}')
    ax.text(_min, 1.22, f'Mean: {mean(data)}')
    ax.text(_min, 1.16, f'Mode: {mode(data)}')

    q1, q2, q3 = quantiles(data, n=4)
    ax.text(_min, 0.8, f'Q1: {q1}')
    ax.text(_min, 0.74, f'Q2: {q2}')
    ax.text(_min, 0.68, f'Q3: {q3}')
    ax.text(_min, 0.62, f'IQR: {q3 - q1}')

    buffer = BytesIO()
    plt.savefig(buffer)
    plt.close()
    buffer.seek(0)
    return discord.File(buffer, 'graph.png')

@to_thread
def plotfn(_, equation: str) -> discord.File:
    def _mul(val):
        val = list(val.group())
        val.insert(-1, "*")
        return "".join(val)

    equation = equation.replace(' ', '')
    equation = re.sub(r"(?<=[0-9x)])x", _mul, equation)
    equation = equation.replace(")(", ")*(")

    x = np.linspace(-100, 100, 50000)

    fn = Expression(equation, ["x"])
    y = [fn(i) for i in x]

    plt.xlim((-40, 40))
    plt.ylim((-40, 40))
    buffer = BytesIO()

    plt.plot(x, y)

    buffer = BytesIO()
    plt.savefig(buffer)
    plt.close()
    buffer.seek(0)
    return discord.File(buffer, 'graph.png')