from copy import deepcopy as dp
from typing import Optional, Type, Union

from mutagen import apev2, monkeysaudio

from .common import TagWrapper
from ..exceptions import UnsupportedImageFormat
from ..utils import get_image_format


class APE(TagWrapper):
    @property
    def tag_type(self) -> Type[monkeysaudio.MonkeysAudio]:
        return monkeysaudio.MonkeysAudio

    @property
    def real_tag(self) -> monkeysaudio.MonkeysAudio:
        return self._real_tag

    @property
    def title(self) -> Optional[apev2.APETextValue]:
        return self.real_tag.get('TITLE')

    @title.setter
    def title(self, value: Union[str, list[str], apev2.APETextValue]) -> None:
        if value is not None:
            self.real_tag['TITLE'] = value

    @property
    def artist(self) -> Optional[apev2.APETextValue]:
        return self.real_tag.get('ARTIST')

    @artist.setter
    def artist(self, value: Union[str, list[str], apev2.APETextValue]) -> None:
        if value is not None:
            self.real_tag['ARTIST'] = value

    @property
    def album(self) -> Optional[apev2.APETextValue]:
        return self.real_tag.get('ALBUM')

    @album.setter
    def album(self, value: Union[str, list[str], apev2.APETextValue]) -> None:
        if value is not None:
            self.real_tag['ALBUM'] = value

    @property
    def comment(self) -> Optional[apev2.APETextValue]:
        return self.real_tag.get('COMMENT')

    @comment.setter
    def comment(self, value: Union[str, list[str], apev2.APETextValue]) -> None:
        if value is not None:
            self.real_tag['COMMENT'] = value

    @property
    def cover(self) -> Optional[apev2.APEBinaryValue]:
        return self.real_tag.get('COVER ART (FRONT)')

    @cover.setter
    def cover(self, value: Union[bytes, apev2.APEBinaryValue]) -> None:
        if value is not None:
            if isinstance(value, bytes):
                image_format: Optional[str] = get_image_format(value)
                if image_format:
                    pic: apev2.APEBinaryValue = apev2.APEBinaryValue(
                        b'Cover Art (Front).' + image_format.encode('ASCII') + b'\x00' + value
                    )
                    pic.type = 3
                else:
                    raise UnsupportedImageFormat(f"'{image_format}'")
            elif isinstance(value, apev2.APEBinaryValue):
                pic: apev2.APEBinaryValue = dp(value)
                pic.type = 3
            else:
                raise TypeError(f'a bytes or mutagen.apev2.APEBinaryValue object required, not {type(value).__name__}')

            self.real_tag['COVER ART (FRONT)'] = pic
