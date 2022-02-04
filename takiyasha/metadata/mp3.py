from copy import deepcopy as dp
from typing import Optional, Type, Union

from mutagen import id3, mp3

from .common import TagWrapper
from ..utils import get_image_mimetype


def _gen_text_frame(
        frame_cls: Type[id3.TextFrame],
        value: Union[str, list[str], id3.TextFrame],
        desc: str = '',
        encoding: int = 3
) -> id3.TextFrame:
    if isinstance(value, id3.TextFrame):
        return value
    else:
        return frame_cls(text=value, encoding=encoding, desc=desc)


class MP3(TagWrapper):
    @property
    def tag_type(self) -> Type[mp3.MP3]:
        return mp3.MP3

    @property
    def real_tag(self) -> mp3.MP3:
        return self._real_tag

    @property
    def title(self) -> Optional[id3.TIT2]:
        return self.real_tag.get('TIT2')

    @title.setter
    def title(self, value: Union[str, list[str], id3.TIT2]) -> None:
        if value is not None:
            self.real_tag['TIT2'] = _gen_text_frame(id3.TIT2, value)

    @property
    def artist(self) -> id3.TPE1:
        return self.real_tag.get('TPE1')

    @artist.setter
    def artist(self, value: Union[str, list[str], id3.TPE1]) -> None:
        if value is not None:
            self.real_tag['TPE1'] = _gen_text_frame(id3.TPE1, value)

    @property
    def album(self) -> id3.TALB:
        return self.real_tag.get('TALB')

    @album.setter
    def album(self, value: Union[str, list[str], id3.TALB]) -> None:
        if value is not None:
            self.real_tag['TALB'] = _gen_text_frame(id3.TALB, value)

    @property
    def comment(self) -> id3.TXXX:
        return self.real_tag.get('TXXX:comment')

    @comment.setter
    def comment(self, value: Union[str, list[str], id3.TXXX]) -> None:
        if value is not None:
            self.real_tag['TXXX:comment'] = _gen_text_frame(id3.TXXX, value, desc='comment')

    @property
    def cover(self) -> id3.APIC:
        return self.real_tag.get('APIC:')

    @cover.setter
    def cover(self, value: Union[bytes, id3.APIC]) -> None:
        if value is not None:
            if isinstance(value, bytes):
                cover: id3.APIC = id3.APIC()
                cover.data = value
                cover.type = 3
                cover.mime = get_image_mimetype(value)
            elif isinstance(value, id3.APIC):
                cover = dp(value)
                cover.type = 3
                cover.mime = get_image_mimetype(cover.data)
            else:
                raise TypeError(f'a bytes or mutagen.id3.APIC object required, not {type(value).__name__}')

            self.real_tag['APIC:'] = cover
