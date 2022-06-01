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
    'BlockSize',
    'ColorFlag',
    'ReplaceColors',
)


class Channels(FlagConverter):
    """• `channel:` R | G | B | RGB (by default `RGB`)
    Specifies the image channel to perform the operation on
    """
    channel: Literal['R', 'G', 'B', 'RGB'] = 'RGB'

class GeneralIntensity(FlagConverter):
    """• `intensity:` an :integer: between `0` and `20` (by default `4`)
    Specifies the intensity for the operation
    """
    intensity: Range[int, 0, 20] = 4

class Degree(FlagConverter):
    """• `degree:` an :integer: between `0` and `360` (by default `180`)
    Specifies the degree for the operation
    """
    degree: Range[int, 0, 360] = 180

class Threshold(Channels):
    """• `channel:` R|G|B|RGB (by default `RGB`)
    Specifies the image channel to perform the operation on
    • `threshold:` a :decimal: between `0` and `1` (by default `0.5`)
    Specifies the threshold amount for the operation
    """
    threshold: Range[float, 0.0, 1.0] = 0.5

class CharcoalIntensity(FlagConverter):
    """• `intensity:` a :decimal: between `0` and `5` (by default `1.5`)
    Specifies the intensity for the operation
    """
    intensity: Range[float, 0.0, 5.0] = 1.5

class LegoSize(FlagConverter):
    """• `size:` an :integer: between `1` and `60` (by default `50`)
    Specifies the number of bricks to use for the generated image
    """
    size: Range[int, 1, 60] = 50

class BlockSize(FlagConverter):
    """• `size:` an :integer: between `1` and `110` (by default `70`)
    Specifies the number of blocks to use for the generated image
    """
    size: Range[int, 1, 110] = 70

class ColorFlag(FlagConverter):
    """• `color:` any valid color in :CSS syntax:
    Specifies the color to use for the operation
    """
    color: ColorConverter

class ReplaceColors(FlagConverter):
    """• `target:` any valid color in :css:
    Specifies the target color to *replace*
    • `to:` any valid color in :css:
    Specifies the color to replace the `target` with
    """
    target: ColorConverter
    to: ColorConverter