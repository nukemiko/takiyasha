from abc import ABCMeta, abstractmethod
from timeit import timeit
from typing import IO, Optional

from ..typehints import BytesType, BytesType_tuple
from ..utils import get_file_ext_by_header


class Cipher(metaclass=ABCMeta):
    """The base class of the cipher class hierarchy.
    
    Subclasses that inherit from this class must implement the method decrypt()."""
    
    def __init__(self, key: Optional[BytesType]):
        """Initialize and return the Cipher instance. See help(type(self)) for accurate signature.
        
        Depending on the algorithm, other parameters may be required.
        
        :param key: The key required for decryption.
                    Can be `None` if no key is required for decryption."""
        if key is None:
            self._key: Optional[bytes] = None
        elif isinstance(key, BytesType_tuple):
            self._key: Optional[bytes] = bytes(key)
        else:
            raise TypeError(f"'key' must be byte or bytearray, not {type(key).__name__}")
    
    @property
    def key(self) -> Optional[bytes]:
        """The key required for decryption."""
        return self._key
    
    @property
    def key_length(self) -> Optional[int]:
        """The length of the key."""
        if self._key is not None:
            key_len: Optional[int] = len(self._key)
        else:
            key_len: Optional[int] = None
        return key_len
    
    @abstractmethod
    def decrypt(self, src_data: BytesType, /, offset: int = 0) -> bytes:
        """Accept the encrypted `src_data` and return the decrypted data.
        
        Provide an `offset` parameter and return the corresponding decrypted data
        according to the starting position of `src_data` in the audio data.
        
        If decryption based on the starting position of `src_data` is not supported,
        the `offset` parameter will be ignored.
        
        :param src_data: The data to be decrypted. Accept bytes or bytearray.
        :param offset: The starting position of `src_data` in the audio data.
                       Default is 0."""


class Decrypter(metaclass=ABCMeta):
    """The base class of the decrypter class hierarchy.
    
    Subclasses that inherit from this class must implement the classmethod new()."""
    
    def __init__(self, **kwargs):
        """Initialize self. See help(type(self)) for accurate signature."""
        self._buffer: IO[bytes] = kwargs.pop('buffer')
        self._cipher: Cipher = kwargs.pop('cipher')
        self._master_key: bytes = kwargs.pop('master_key')
        self._audio_start: int = kwargs.pop('audio_start')
        self._audio_length: int = kwargs.pop('audio_length')
        
        self._buffer.seek(self._audio_start, 0)
    
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
    def audio_end(self) -> int:
        """The offset of the ending position of the audio data."""
        return self.audio_start + self.audio_length
    
    @property
    def audio_format(self) -> Optional[str]:
        """The format of the audio data.
        
        Returns `None` when the audio format is unrecognized."""
        offset_orig: int = self.buffer.tell()
        self.reset_buffer_offset()
        
        decrypted: bytes = self.cipher.decrypt(self.buffer.read(32))
        
        self.buffer.seek(offset_orig, 0)
        
        return get_file_ext_by_header(decrypted)
    
    def reset_buffer_offset(self) -> int:
        """Change the stream position of `self.buffer`
        to the offset of the starting position of the audio data.
        
        The offset of the starting position of the audio data
        is given by `self.audio_start`."""
        return self.buffer.seek(self.audio_start, 0)
    
    def benchmark(self, test_size: int = 1048576) -> float:
        """Calculate the time required to decrypt data of the `test_size` specified size.

        The default value of `test_size` is 1048576 - 1 MiB."""
        offset_orig: int = self.buffer.tell()
        self.reset_buffer_offset()
        
        stmt: str = """self.read(test_size)"""
        result: float = timeit(stmt, globals=locals(), number=1)
        
        self.buffer.seek(offset_orig, 0)
        
        return result
    
    def read(self, size: int = -1, /) -> bytes:
        """Read up to size bytes from `self.buffer`
        and return size bytes of decrypted data. This is not equal to self.buffer.read().
        
        As a convenience, if size is unspecified or -1,
        returns all decrypted data from the file pointer position of self.buffer
        to the end of the audio data."""
        
        # If the file pointer position of self.buffer is bigger than
        # the ending position of audio data, empty bytestring will be returned.
        #
        # If the file pointer position of self.buffer is smaller than
        # the position of the starting position of audio data,
        # will seek to the starting position of audio data before reading.
        #
        # `self.reset_buffer_offset()` should be called before calling this method,
        # otherwise incorrect or empty data may be returned.
        #
        # If the `reset_buffer_offset` parameter is specified as True,
        # the self.reset_buffer_offset() will be called automatically before reading.
        #
        # :param size: The size of decrypted data to be read. Default is -1.
        # :param reset_buffer_offset: Whether call the self.reset_buffer_offset() before reading."""
        offset: int = self.buffer.tell() - self.audio_start
        if offset < 0:
            offset = 0
        
        if size < 0:
            size = self.audio_length
        
        data: bytes = self.buffer.read(size)
        
        return self.cipher.decrypt(data, offset=offset)
    
    @classmethod
    @abstractmethod
    def new(cls, file: IO[bytes]):
        """Create a new Decrypter.
        
        :param file: The file to be decrypted.
                     Must be a readable and seekable file object."""
