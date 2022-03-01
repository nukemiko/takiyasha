from copy import deepcopy as dp
from typing import IO, Optional, Type, Union

from mutagen import flac

from .common import TagWrapper
from ..typehints import PathType
from ..utils import get_image_mimetype


class FLAC(TagWrapper):
    def __init__(self, filething: Union[PathType, IO[bytes]]):
        super().__init__(filething)
        if self.real_tag.get('descripition') and not self.real_tag.get('description'):
            self.real_tag['description'] = self.real_tag.pop('descripition')

    @property
    def tag_type(self) -> Type[flac.FLAC]:
        return flac.FLAC

    @property
    def real_tag(self) -> flac.FLAC:
        return self._real_tag

    @property
    def title(self) -> list[str]:
        return self.real_tag.get('title')

    @title.setter
    def title(self, value: Union[str, list[str]]) -> None:
        if value is not None:
            self.real_tag['title'] = value

    @property
    def artist(self) -> list[str]:
        return self.real_tag.get('artist')

    @artist.setter
    def artist(self, value: Union[str, list[str]]) -> None:
        if value is not None:
            self.real_tag['artist'] = value

    @property
    def album(self) -> list[str]:
        return self.real_tag.get('album')

    @album.setter
    def album(self, value: Union[str, list[str]]) -> None:
        if value is not None:
            self.real_tag['album'] = value

    @property
    def comment(self) -> list[str]:
        return self.real_tag.get('description')

    @comment.setter
    def comment(self, value: Union[str, list[str]]) -> None:
        if value is not None:
            self.real_tag['description'] = value

    @property
    def cover(self) -> flac.Picture:
        pictures: list[flac.Picture] = self.real_tag.pictures
        for item in pictures:
            if item.type == 3:
                return item

    @cover.setter
    def cover(self, value: Union[bytes, flac.Picture]):
        if value is not None:
            self.set_picture(value, 3)

    @property
    def pictures(self) -> list[flac.Picture]:
        return self.real_tag.pictures

    @pictures.setter
    def pictures(self, value: Union[flac.Picture, list[flac.Picture]]) -> None:
        if value is not None:
            if isinstance(value, flac.Picture):
                pictures: list[flac.Picture] = [dp(value)]
            else:
                pictures: list[flac.Picture] = dp(value)

            self.real_tag.clear_pictures()
            for item in pictures:
                self.real_tag.add_picture(item)

    def set_picture(
            self,
            picture: Union[bytes, flac.Picture],
            content_type: int = None,
            mime: str = None,
            desc: str = ''
    ) -> None:
        if picture is not None:
            if isinstance(picture, flac.Picture):
                pic: flac.Picture = dp(picture)
                if content_type is not None:
                    pic.type = content_type
                if mime is not None:
                    pic.mime = mime
                if desc:
                    pic.desc = desc
            elif isinstance(picture, bytes):
                pic: flac.Picture = flac.Picture()
                pic.data = picture
                if content_type is None:
                    content_type: int = 3
                if mime is None:
                    mime: str = get_image_mimetype(pic.data)
                if desc is None:
                    desc: str = ''
                pic.type = content_type
                pic.mime = mime
                pic.desc = desc
            else:
                raise TypeError(f'a bytes or mutagen.flac.Picture object required, not {type(picture).__name__}')

            pictures: list[Optional[flac.Picture]] = dp(self.real_tag.pictures)
            for idx, item in enumerate(pictures):
                if item.type == pic.type:
                    pictures[idx] = None
            pictures: list[Optional[flac.Picture]] = list(filter(None, pictures))

            pictures.append(pic)

            self.real_tag.clear_pictures()
            for item in pictures:
                self.real_tag.add_picture(item)
