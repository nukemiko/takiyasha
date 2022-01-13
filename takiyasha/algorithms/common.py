from abc import ABCMeta, abstractmethod
from typing import IO, Optional

from takiyasha.typehints import BytesType, BytesType_tuple


class Cipher(metaclass=ABCMeta):
    """The base class of the cipher class hierarchy.
    
    You cannot directly call it, because it is designed as a template
    for other ciphers.
    
    Subclasses that inherit from this class must implement the decrypt() method."""
    
    def __init__(self, key: Optional[BytesType]):
        """Initialize self. See help(type(self)) for accurate signature."""
        if key is None:
            self._key: Optional[bytes] = None
        elif isinstance(key, BytesType_tuple):
            self._key: Optional[bytes] = bytes(key)
        else:
            raise TypeError(f"'key' must be byte or bytearray, not {type(key).__name__}")
    
    @property
    def key(self) -> Optional[bytes]:
        return self._key
    
    @property
    def key_length(self) -> Optional[int]:
        if self._key is not None:
            key_len: Optional[int] = len(self._key)
        else:
            key_len: Optional[int] = None
        return key_len
    
    @abstractmethod
    def decrypt(self, src_data: BytesType, /, offset: int = 0):
        """Accept encrypted src_data and return the decrypted data."""
        pass


class Decrypter(metaclass=ABCMeta):
    def __init__(self, **kwargs):
        self._buffer: IO[bytes] = kwargs.pop('buffer')
        self._cipher: Cipher = kwargs.pop('cipher')
        self._master_key: bytes = kwargs.pop('master_key')
        self._audio_start: int = kwargs.pop('audio_start')
        self._audio_length: int = kwargs.pop('audio_length')
        
        self._parameters: dict[str, ...] = kwargs.copy()
        
        self._buffer.seek(0, 0)
    
    @property
    def buffer(self) -> IO[bytes]:
        return self._buffer
    
    @property
    def cipher(self) -> Cipher:
        return self._cipher
    
    @property
    def master_key(self) -> bytes:
        return self._master_key
    
    @property
    def audio_start(self) -> int:
        return self._audio_start
    
    @property
    def audio_length(self) -> int:
        return self._audio_start
    
    @abstractmethod
    @property
    def audio_format(self) -> str:
        pass
    
    def reset_buffer_offset(self) -> int:
        return self.buffer.seek(self.audio_start, 0)
    
    def read(self, size: int = -1, /) -> bytes:
        offset: int = self.buffer.tell()
        data: bytes = self.buffer.read(size)
        return self.cipher.decrypt(data, offset=offset)
    
    @classmethod
    @abstractmethod
    def generate(cls, file: IO[bytes]):
        pass
