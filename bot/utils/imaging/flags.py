"""
Contains FlagConverters for imaging commands
"""
from typing import Literal

from discord.ext.commands import FlagConverter, Range

from .converter import ColorConverter

__all__: tuple[str, ...] = (
    'Channels',
    'GeneralIntensity',
    'Degree',
    'Threshold',
    'CharcoalIntensity',
    'LegoSize',
    'McSize',
    'ColorFlag',
    'ReplaceColors',
)


class Channels(FlagConverter):
    channel: Literal['R', 'G', 'B', 'RGB'] = 'RGB'

class GeneralIntensity(FlagConverter):
    intensity: Range[int, 0, 20] = 4

class Degree(FlagConverter):
    degree: Range[int, 0, 360] = 180

class Threshold(Channels):
    threshold: Range[float, 0.0, 1.0] = 0.5

class CharcoalIntensity(Channels):
    intensity: Range[float, 0.0, 5.0] = 1.5

class LegoSize(FlagConverter):
    size: Range[int, 2, 60] = 50

class McSize(FlagConverter):
    size: Range[int, 2, 60] = 70

class ColorFlag(FlagConverter):
    color: ColorConverter

class ReplaceColors(FlagConverter):
    target: ColorConverter
    to: ColorConverter