from abc import ABCMeta, abstractmethod
from typing import IO, Optional, Type, Union

from mutagen import FileType

from ..typehints import PathType


class TagWrapper(metaclass=ABCMeta):
    @property
    @abstractmethod
    def tag_type(self) -> Optional[Type[FileType]]:
        pass

    def __init__(self, filething: Union[PathType, IO[bytes]]):
        if self.tag_type:
            self._real_tag = self.tag_type(filething)
        else:
            self._real_tag = None
        self._filething: Union[PathType, IO[bytes]] = filething
        if hasattr(self._filething, 'seek'):
            self._filething.seek(0, 0)

    @property
    def filething(self) -> Union[PathType, IO[bytes]]:
        return self._filething

    @property
    def real_tag(self) -> FileType:
        return self._real_tag

    @property
    @abstractmethod
    def title(self):
        pass

    @title.setter
    @abstractmethod
    def title(self, value):
        pass

    @property
    @abstractmethod
    def artist(self):
        pass

    @artist.setter
    @abstractmethod
    def artist(self, value):
        pass

    @property
    @abstractmethod
    def album(self):
        pass

    @album.setter
    @abstractmethod
    def album(self, value):
        pass

    @property
    @abstractmethod
    def comment(self):
        pass

    @comment.setter
    @abstractmethod
    def comment(self, value):
        pass

    @property
    @abstractmethod
    def cover(self):
        pass

    @cover.setter
    @abstractmethod
    def cover(self, value):
        pass

    def save(self, *args, **kwargs):
        if self.real_tag is not None:
            self.real_tag.save(*args, **kwargs)
