from abc import ABCMeta, abstractmethod
from typing import IO, Type, Union

from mutagen import FileType

from ..typehints import PathType


class TagProxy(metaclass=ABCMeta):
    @property
    @abstractmethod
    def tag_type(self) -> Type[FileType]:
        pass
    
    def __init__(self, filething: Union[PathType, IO[bytes]]):
        self._filething: Union[PathType, IO[bytes]] = filething
        self._filething_seekable: bool = False
        if getattr(filething, 'read', None) and getattr(filething, 'seek', None):
            self._filething_seekable: bool = True
            self._filething.seek(0, 0)
        self._real_tag = self.tag_type(self._filething)
    
    @property
    def filething(self) -> Union[PathType, IO[bytes]]:
        return self._filething
    
    @property
    def filething_seekable(self) -> bool:
        return self._filething_seekable
    
    @property
    def real_tag(self):
        return self._real_tag
    
    def save(self):
        if self._filething_seekable:
            self._filething.seek(0, 0)
            self._real_tag.save(self._filething)
            self._filething.seek(0, 0)
        else:
            self._real_tag.save(self._filething)
