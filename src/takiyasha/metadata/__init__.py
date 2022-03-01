from typing import IO, Optional, Type, Union

from .ape import APE
from .common import TagWrapper
from .flac import FLAC
from .m4a import M4A
from .mp3 import MP3
from .ogg import OGG
from ..exceptions import UnsupportedTagFormat
from ..typehints import PathType
from ..utils import get_audio_format, get_file_name_from_fileobj, is_fileobj

SUPPORTED_AUDIO_FORMATS = {
    'ape': APE,
    'flac': FLAC,
    'm4a': M4A,
    'mp3': MP3,
    'ogg': OGG
}


def get_tag_wrapper_class(audiofmt: str) -> Optional[Type[TagWrapper]]:
    return SUPPORTED_AUDIO_FORMATS.get(audiofmt)


def new_tag(filething: Union[PathType, IO[bytes]]) -> TagWrapper:
    if is_fileobj(filething):
        file: IO[bytes] = filething
        file_name: str = get_file_name_from_fileobj(file)
        file_can_be_closed: bool = False
    else:
        file: IO[bytes] = open(filething, 'rb')
        file_name: str = filething
        file_can_be_closed: bool = True
    file.seek(0, 0)
    audiofmt: Optional[str] = get_audio_format(file.read(32))
    if file_can_be_closed:
        file.close()
    else:
        file.seek(0, 0)

    tag_cls: Type[TagWrapper] = get_tag_wrapper_class(audiofmt)
    if not tag_cls:
        raise UnsupportedTagFormat(f"file '{file_name}' is in an unrecongized format")

    return tag_cls(filething)
