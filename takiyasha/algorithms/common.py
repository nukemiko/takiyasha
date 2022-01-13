from abc import ABCMeta, abstractmethod
from typing import IO, Optional

from ..typehints import BytesType, BytesType_tuple
from ..utils import get_file_ext_by_header


class Cipher(metaclass=ABCMeta):
    """The base class of the cipher class hierarchy.
    
    You cannot directly call it, because it is designed as a template
    for other ciphers.
    
    Subclasses that inherit from this class must implement the method decrypt()."""
    
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
    """The base class of the decrypter class hierarchy.
    
    You cannot directly call it, because it is designed as a template
    for other ciphers.
    
    Subclasses that inherit from this class must implement the classmethod new()."""
    
    def __init__(self, **kwargs):
        """Initialize self. See help(type(self)) for accurate signature."""
        self._buffer: IO[bytes] = kwargs.pop('buffer')
        self._cipher: Cipher = kwargs.pop('cipher')
        self._master_key: bytes = kwargs.pop('master_key')
        self._audio_start: int = kwargs.pop('audio_start')
        self._audio_length: int = kwargs.pop('audio_length')
        
        self._buffer.seek(0, 0)
    
    @property
    def buffer(self) -> IO[bytes]:
        """File object pointing to the source file."""
        return self._buffer
    
    @property
    def cipher(self) -> Cipher:
        """Instance of the cipher used by the file."""
        return self._cipher
    
    @property
    def master_key(self) -> bytes:
        """The key used for encryption of the audio data."""
        return self._master_key
    
    @property
    def audio_start(self) -> int:
        """The offset of the starting position of the audio data."""
        return self._audio_start
    
    @property
    def audio_length(self) -> int:
        """The length of the audio data."""
        return self._audio_length
    
    @property
    def audio_format(self) -> Optional[str]:
        """The format of the audio data.
        
        Returns `None` when the audio format is unrecognized."""
        offset_orig: int = self.buffer.tell()
        self.buffer.seek(self.audio_start, 0)
        
        decrypted: bytes = self.cipher.decrypt(self.buffer.read(16))
        
        self.buffer.seek(offset_orig, 0)
        
        return get_file_ext_by_header(decrypted)
    
    def reset_buffer_offset(self) -> int:
        """Change the stream position of `self.buffer`
        to the offset of the starting position of the audio data.
        
        The offset of the starting position of the audio data
        is given by `self.audio_start`."""
        return self.buffer.seek(self.audio_start, 0)
    
    def read(self, size: int = -1, /) -> bytes:
        """Read up to size bytes from `self.buffer`
        and return size bytes of decrypted data.
        
        As a convenience, if size is unspecified or -1,
        all decrypted data until EOF are returned.
        
        `self.reset_buffer_offset()` should be called before calling this method,
        otherwise incorrect data may be returned."""
        if size < 0:
            size = self.audio_length
        
        offset: int = self.buffer.tell() - self.audio_start
        if offset < 0:
            offset = 0
        data: bytes = self.buffer.read(size)
        
        return self.cipher.decrypt(data, offset=offset)
    
    @classmethod
    @abstractmethod
    def new(cls, file: IO[bytes]):
        """Create a new Decrypter."""
        pass
