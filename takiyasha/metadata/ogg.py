from base64 import b64decode, b64encode
from copy import deepcopy as dp
from typing import IO, Optional, Type, Union

from mutagen import flac, oggvorbis

from .common import TagWrapper
from ..typehints import PathType
from ..utils import get_image_mimetype


class OGG(TagWrapper):
    def __init__(self, filething: Union[PathType, IO[bytes]]):
        super().__init__(filething)
        if self.real_tag.get('descripition') and not self.real_tag.get('description'):
            self.real_tag['description'] = self.real_tag.pop('descripition')

    @property
    def tag_type(self) -> Type[oggvorbis.OggVorbis]:
        return oggvorbis.OggVorbis

    @property
    def real_tag(self) -> oggvorbis.OggVorbis:
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
    def cover(self) -> Optional[flac.Picture]:
        # 如果封面以 Theora 视频流形式嵌入文件，则无法通过此属性获取封面
        metadata_block_pictures: list[bytes] = self.real_tag.get('metadata_block_picture', [])

        for raw_picdata_b64 in metadata_block_pictures:
            try:
                raw_picdata: bytes = b64decode(raw_picdata_b64)
            except (TypeError, ValueError):
                continue

            try:
                picture = flac.Picture(data=raw_picdata)
            except flac.error:
                continue

            if picture.type == 3:
                return picture

    @cover.setter
    def cover(self, value: Union[bytes, flac.Picture]) -> None:
        if value is not None:
            if isinstance(value, bytes):
                picture: flac.Picture = flac.Picture()
                picture.data = value
                picture.mime = get_image_mimetype(value)
                picture.type = 3
            elif isinstance(value, flac.Picture):
                picture = dp(value)
                picture.mime = get_image_mimetype(picture.data)
                picture.type = 3
            else:
                raise TypeError(f'a bytes or mutagen.flac.Picture object required, not {type(value).__name__}')

            data: bytes = picture.write()
            encoded_data: bytes = b64encode(data)
            metadata_block_picture_data = encoded_data.decode('ASCII')

            self.real_tag['metadata_block_picture'] = [metadata_block_picture_data]
