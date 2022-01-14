import base64
from typing import IO, Optional, Type, Union

from mutagen import flac, oggvorbis

from .common import TagProxy
from ..typehints import PathType


class Ogg(TagProxy):
    @property
    def tag_type(self) -> Type[oggvorbis.OggVorbis]:
        return oggvorbis.OggVorbis
    
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
    def comment(self):
        return
    
    @comment.setter
    def comment(self, value: str):
        return
    
    @property
    def cover(self) -> list[flac.Picture]:
        results: list[flac.Picture] = []
        for b64_data in self._real_tag.get('metadata_block_picture', []):
            try:
                data = base64.b64decode(b64_data)
            except (TypeError, ValueError):
                continue
            
            try:
                picture = flac.Picture(data)
            except flac.error:
                continue
            else:
                results.append(picture)
        
        return results
    
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
        
        vcomment_value: str = base64.b64encode(cover.write()).decode('ascii')
        
        self._real_tag['metadata_block_picture'] = [vcomment_value]
