
import humanize

__all__: tuple[str] = (
    'BaseImageException',
    'TooManyFrames',
    'InvalidColor',
    'ImageTooLarge',
    'ImageProcessTimeout',
)


class BaseImageException(Exception):
    message: str

    def __str__(self) -> str:
        if hasattr(self, 'message'):
            return self.message
        else:
            return str(super())

class TooManyFrames(BaseImageException):

    def __init__(self, count: int, max_frames: int) -> None:
        self.message = f'Provided image has a frame-count of `{count}` which exeeds the limit of `{max_frames}`'
        super().__init__(self.message)

class InvalidColor(BaseImageException):

    def __init__(self, argument: str) -> None:
        self.message = f'`{argument}` is not a valid color!'
        super().__init__(self.message)

class ImageTooLarge(BaseImageException):

    def __init__(self, size: int, max_size: int = 15_000_000) -> None:
        MIL = 1_000_000
        self.message = (
            f'The size of the provided image (`{size / MIL:.2f} MB`) '
            f'exceeds the limit of `{max_size / MIL} MB`'
        )
        super().__init__(self.message)

class ImageProcessTimeout(BaseImageException):

    def __init__(self, timeout: int) -> None:
        timeout = humanize.precisedelta(timeout)
        self.message = f'Image Process took too long and timed out, the timeout is `{timeout}`'
        super().__init__(self.message)