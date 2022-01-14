from typing import IO, Optional, Type, Union

from mutagen import id3, mp3

from .common import TagProxy
from ..typehints import PathType


class Mp3(TagProxy):
    @property
    def tag_type(self) -> Type[mp3.MP3]:
        return mp3.MP3
    
    def __init__(self, filething: Union[PathType, IO[bytes]]):
        super().__init__(filething)
    
    @property
    def title(self) -> Optional[id3.TIT2]:
        return self._real_tag.get('TIT2')
    
    @title.setter
    def title(self, value: str):
        self._real_tag['TIT2'] = id3.TIT2(text=[value], encoding=3)
    
    @property
    def artist(self) -> Optional[id3.TPE1]:
        return self._real_tag.get('TPE1')
    
    @artist.setter
    def artist(self, value: str):
        self._real_tag['TPE1'] = id3.TPE1(text=[value], encoding=3)
    
    @property
    def album(self) -> Optional[id3.TALB]:
        return self._real_tag.get('TALB')
    
    @album.setter
    def album(self, value: str):
        self._real_tag['TALB'] = id3.TALB(text=[value], encoding=3)
    
    @property
    def comment(self) -> Optional[id3.TXXX]:
        return self._real_tag.get('TXXX:comment')
    
    @comment.setter
    def comment(self, value: str):
        self._real_tag['TXXX:comment'] = id3.TXXX(text=[value], desc='comment', encoding=3)
    
    @property
    def cover(self) -> Optional[id3.APIC]:
        return self._real_tag.get('APIC:')
    
    def set_cover(self, cover_data: bytes, content_type: int = 3):
        cover: id3.APIC = id3.APIC()
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
        
        self._real_tag['APIC:'] = cover
