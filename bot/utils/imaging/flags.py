"""
Contains FlagConverters for imaging commands
"""
from typing import Literal

from discord.ext.commands import FlagConverter, Range

__all__: tuple[str, ...] = (
    'Channels',
    'GeneralIntensity',
    'Degree',
    'Solarize',
    'LegoSize',
    'McSize',
)


class Channels(FlagConverter):
    channel: Literal['R', 'G', 'B', 'RGB'] = 'RGB'

class GeneralIntensity(FlagConverter):
    intensity: Range[int, 0, 20] = 4

class Degree(FlagConverter):
    degree: Range[int, 0, 360] = 180

class Solarize(Channels):
    threshold: Range[float, 0.0, 1.0] = 0.5

class LegoSize(FlagConverter):
    size: Range[int, 2, 60] = 50

class McSize(FlagConverter):
    size: Range[int, 2, 60] = 70