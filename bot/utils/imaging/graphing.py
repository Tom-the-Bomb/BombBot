from __future__ import annotations

from typing import TYPE_CHECKING
from io import BytesIO
from statistics import (
    mean,
    mode,
    quantiles,
    StatisticsError,
)

import numpy as np
import matplotlib
matplotlib.use('agg')

from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties
plt.style.use(('bmh', 'ggplot'))

import discord
from sympy import Symbol, Basic
from sympy.parsing.sympy_parser import (
    parse_expr,
    convert_xor,
    standard_transformations,
    implicit_multiplication_application
)

from ..helpers import to_thread, get_asset

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

__all__: tuple[str, ...] = (
    'boxplot',
    'plotfn',
)

CODEFONT: FontProperties = FontProperties(
    fname=get_asset('Monaco-Linux.ttf'),
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
        labels=['A'],
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

    x = ax.get_xticks()[1]

    _min, _max = min(data), max(data)
    ax.text(x, 1.4, f'Min: {_min}',
        fontproperties=CODEFONT,
    )
    ax.text(x, 1.34, f'Max: {_max}',
        fontproperties=CODEFONT,
    )
    ax.text(x, 1.28, f'Range: {_max - _min}',
        fontproperties=CODEFONT,
    )
    ax.text(x, 1.22, f'Mean: {mean(data)}',
        fontproperties=CODEFONT,
    )
    ax.text(x, 1.16, f'Mode: {mode(data)}',
        fontproperties=CODEFONT,
    )

    try:
        q1, q2, q3 = quantiles(data, n=4)
    except StatisticsError:
        q1 = q2 = q3 = data[0]

    ax.text(x, 0.8, f'Q1: {q1}',
        fontproperties=CODEFONT,
    )
    ax.text(x, 0.74, f'Q2: {q2}',
        fontproperties=CODEFONT,
    )
    ax.text(x, 0.68, f'Q3: {q3}',
        fontproperties=CODEFONT,
    )
    ax.text(x, 0.62, f'IQR: {q3 - q1}',
        fontproperties=CODEFONT,
    )

    buffer = BytesIO()
    plt.savefig(buffer)
    plt.close()
    buffer.seek(0)
    return discord.File(buffer, 'graph.png')

@to_thread
def plotfn(_,
    equation: str,
    *,
    xrange: tuple[int, int] = None,
    polar: bool = False
) -> discord.File:
    def f(x):
        expr: Basic = parse_expr(
            equation,
            transformations=(
                standard_transformations +
                (convert_xor,) +
                (implicit_multiplication_application,)
            )
        )
        _vars = list(expr.atoms(Symbol))
        if _vars:
            expr = expr.subs(_vars[0], x)
        try:
            float(expr)
            return expr
        except TypeError:
            return

    if polar:
        theta = np.linspace(*(xrange or (0, 38)), 1000) # [0, ~12pi]

        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
        ax.set_title(f'r = {equation}', va='bottom')
        ax.plot(theta, np.vectorize(f)(theta))
    else:
        fig: Figure = plt.figure()
        ax: Axes = fig.add_subplot(1, 1, 1)
        ax.set_title(f'y = {equation}', pad=15)
        x = np.linspace(*(xrange or (-20, 20)), 1000)

        ax.set_aspect('equal', adjustable='box')
        ax.spines['left'].set_position('center')
        ax.spines['bottom'].set_position('zero')
        ax.spines['right'].set_color('none')
        ax.spines['top'].set_color('none')
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        ax.set_ylim(*ax.get_xlim())

        ax.plot(x, np.vectorize(f)(x))
        plt.axis('equal')

    buffer = BytesIO()
    plt.savefig(buffer)
    plt.close()
    buffer.seek(0)
    return discord.File(buffer, 'graph.png')