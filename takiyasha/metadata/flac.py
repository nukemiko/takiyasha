from typing import IO, Optional, Type, Union

from mutagen import flac

from .common import TagProxy
from ..typehints import PathType


class Flac(TagProxy):
    @property
    def tag_type(self) -> Type[flac.FLAC]:
        return flac.FLAC
    
    def __init__(self, filething: Union[PathType, IO[bytes]]):
        super().__init__(filething)
    
    @property
    def title(self) -> Optional[list[str]]:
        return self._real_tag.get('title')
    
    @title.setter
    def title(self, value: str):
        self._real_tag['title'] = value
    
    @property
    def artist(self) -> Optional[list[str]]:
        return self._real_tag.get('artist')
    
    @artist.setter
    def artist(self, value: str):
        self._real_tag['artist'] = value
    
    @property
    def album(self) -> Optional[list[str]]:
        return self._real_tag.get('album')
    
    @album.setter
    def album(self, value: str):
        self._real_tag['album'] = value
    
    @property
    def comment(self) -> Optional[list[str]]:
        return self._real_tag.get('description')
    
    @comment.setter
    def comment(self, value: str):
        self._real_tag['description'] = value
    
    @property
    def cover(self) -> list[flac.Picture]:
        return self._real_tag.pictures
    
    def set_cover(self, cover_data: bytes, content_type: int = 3):
        cover: flac.Picture = flac.Picture()
        try:
            if cover_data.startswith(b'\x89PNG'):
                cover.mime = 'image/png'
            elif cover_data.startswith(b'\xff\xd8\xff'):
                cover.mime = 'image/jpeg'
            else:
                raise ValueError('unsupported cover data format')
        except TypeError:
            return
        cover.type = content_type
        cover.data = cover_data
        
        self._real_tag.clear_pictures()
        self._real_tag.add_picture(cover)
