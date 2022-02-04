from copy import deepcopy as dp
from typing import Optional, Type, Union

from mutagen import mp4

from .common import TagWrapper
from ..exceptions import UnsupportedImageFormat
from ..utils import get_image_format

_SUPPORTED_PICTURE_TYPES: dict[str, int] = {
    'jpg': 13,
    'png': 14,
    'bmp': 27
}


class M4A(TagWrapper):
    @property
    def tag_type(self) -> Type[mp4.MP4]:
        return mp4.MP4

    @property
    def real_tag(self) -> mp4.MP4:
        return self._real_tag

    @property
    def title(self) -> Optional[list[str]]:
        return self.real_tag.get('©nam')

    @title.setter
    def title(self, value: Union[str, list[str]]) -> None:
        self.real_tag['©nam'] = value

    @property
    def artist(self) -> Optional[list[str]]:
        return self.real_tag.get('©ART')

    @artist.setter
    def artist(self, value: Union[str, list[str]]) -> None:
        self.real_tag['©ART'] = value

    @property
    def album(self) -> Optional[list[str]]:
        return self.real_tag.get('©alb')

    @album.setter
    def album(self, value: Union[str, list[str]]) -> None:
        self.real_tag['©alb'] = value

    @property
    def comment(self) -> Optional[list[str]]:
        return self.real_tag.get('©cmt')

    @comment.setter
    def comment(self, value: Union[str, list[str]]) -> None:
        self.real_tag['©cmt'] = value

    @property
    def cover(self) -> Optional[mp4.MP4Cover]:
        pictures: Optional[list[mp4.MP4Cover]] = self.real_tag.get('covr')
        if pictures:
            return pictures[0]

    @cover.setter
    def cover(self, value: Union[bytes, mp4.MP4Cover]) -> None:
        if isinstance(value, bytes):
            picfmt: Optional[str] = get_image_format(value)
            if not picfmt:
                raise UnsupportedImageFormat(f"'{picfmt}'")
            pic: mp4.MP4Cover = mp4.MP4Cover(value, _SUPPORTED_PICTURE_TYPES[picfmt])
        elif isinstance(value, mp4.MP4Cover):
            pic: mp4.MP4Cover = value
            picfmt: Optional[str] = get_image_format(bytes(pic))
            if picfmt:
                pic.imageformat = _SUPPORTED_PICTURE_TYPES[picfmt]
        else:
            raise TypeError(f'a bytes or mutagen.mp4.MP4Cover object required, not {type(value).__name__}')

        covers: Optional[list[mp4.MP4Cover]] = dp([self.real_tag.get('covr')])
        if covers:
            covers[0] = pic
        else:
            covers = [pic]

        self.real_tag['covr'] = covers
