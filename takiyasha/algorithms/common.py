from abc import ABCMeta, abstractmethod
from io import BufferedIOBase
from timeit import timeit
from typing import BinaryIO, IO, Optional, TypeVar, Union

from ..typehints import (
    BytesType,
    BytesType_tuple,
    PathType,
    WritableBuffer,
    WritableBuffer_tuple
)
from ..utils import (
    get_file_ext_by_header,
    get_file_name_from_fileobj,
    is_fileobj,
    raise_while_not_fileobj
)


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


class StreamCipher(metaclass=ABCMeta):
    """为构建一个流密码提供的基础层次结构。"""

    def __init__(self, key: Optional[bytes]):
        """根据密钥和其他参数（如果有）初始化并返回一个密码实例。

        Args:
            key: 构建密码所需的密钥"""
        if key is not None:
            if not isinstance(key, bytes):
                raise TypeError(f"'key' must be bytes or None, not {type(key).__name__}")
            self._key: Optional[bytes] = key
            self._key_len: Optional[int] = len(key)
        else:
            self._key: Optional[bytes] = None
            self._key_len: Optional[int] = None

    @property
    def key(self) -> Optional[bytes]:
        """构建密码所需的密钥。"""
        return self._key

    @property
    def key_length(self) -> Optional[int]:
        """密钥的长度。"""
        return self._key_len

    @abstractmethod
    def decrypt(self, src: bytes, offset: int = 0) -> bytes:
        """将传入的源数据解密，并返回解密后的数据。

        此方法不会检查解密后数据的正确性，您应当自行完成这一步骤。

        Args:
            src: 需要解密的源数据。
            offset: 源数据在源文件中的起始位置。
                    如果解密过程不依赖此参数，为它指定的任何值都会被忽略。
        Returns:
            解密后的数据。"""


class BlockCipher(metaclass=ABCMeta):
    """为构建一个分组密码提供的基础层次结构。"""

    def __init__(self, key: Optional[bytes]):
        """根据密钥和其他参数（如果有）初始化并返回一个密码实例。

        Args:
            key: 构建密码所需的密钥"""
        if key is not None:
            if not isinstance(key, bytes):
                raise TypeError(f"'key' must be bytes or None, not {type(key).__name__}")
            self._key: Optional[bytes] = key
            self._key_len: Optional[int] = len(key)
        else:
            self._key: Optional[bytes] = None
            self._key_len: Optional[int] = None

    @property
    @abstractmethod
    def blocksize(self) -> int:
        """分组密码采用的块大小，为一个整数。"""
        pass

    @property
    def key(self) -> Optional[bytes]:
        """构建密码所需的密钥。"""
        return self._key

    @property
    def key_length(self) -> Optional[int]:
        """密钥的长度。"""
        return self._key_len

    @abstractmethod
    def decrypt(self, src: bytes) -> bytes:
        """将传入的源数据解密，并返回解密后的数据。

        此方法不会检查解密后数据的正确性，您应当自行完成这一步骤。

        Args:
            src: 需要解密的源数据。
        Returns:
            解密后的数据。"""


CipherTypeVar = TypeVar('CipherTypeVar', StreamCipher, BlockCipher)
"""用于表示 StreamCipher 和 BlockCipher，以及继承自两者的子类的类型变量。"""


class Decoder(BufferedIOBase, BinaryIO, metaclass=ABCMeta):
    """为构建一个解码器提供的基础层次结构。

    这个基类实现了一个只读且可从任意位置读取的缓冲二进制流，使用加密的音频数据作为缓冲区，
    在读取时返回解密的数据。"""

    @classmethod
    def new(cls, filething: Union[PathType, IO[bytes]]):
        """创建并返回一个新的解码器实例。

        Args:
            filething: 文件路径或文件对象。
                       若为路径，指向的必须是可读取的文件；
                       若为文件对象，必须可读取且支持从任意位置读取。
        Returns:
            新的解码器实例。"""
        if is_fileobj(filething):
            raise_while_not_fileobj(filething, seekable=True, readable=True)
            file: IO[bytes] = filething
        else:
            file: IO[bytes] = open(filething, 'rb')

        raw_audio_data, cipher, misc = cls._pre_create_instance(file)
        file_name: str = get_file_name_from_fileobj(file)

        return cls(raw_audio_data, cipher, misc, file_name)

    @classmethod
    @abstractmethod
    def _pre_create_instance(cls, file: IO[bytes]) -> tuple[bytes, CipherTypeVar, dict[str, ...]]:
        """从文件中获取并返回创建解码器实例所需的信息。

        没有这些信息就无法创建解码器实例，因此这是一个必须实现的抽象方法。

        Args:
            file: 文件对象
        Returns:
            一个包含了加密的音频数据、根据加密类型创建的密码实例，以及其他信息（例如元数据等）的元组。"""

    def __init__(
            self,
            raw_audio_data: bytes,
            cipher: CipherTypeVar,
            misc: dict[str, ...],
            filename: str
    ):
        """根据加密音频数据、密码实例和其他信息（如果有）初始化并返回一个解码器实例。

        Args:
            raw_audio_data: 加密的音频数据，在实例中作为缓冲区
            cipher: 根据加密类型创建的密码实例
            misc: 其他信息（例如元数据等）"""
        self._offset: int = 0
        self._raw_audio_data: bytes = raw_audio_data
        self._audio_length: int = len(raw_audio_data)
        self._filename: str = filename
        self._cipher: CipherTypeVar = cipher
        self._misc: dict[str, ...] = misc

    def get_raw_audio_data(self) -> bytes:
        """以字节的形式返回原始的加密音频数据。

        读取解密的音频数据，需要使用 read()、read1() 或 readinto()、readinto1()。"""
        self._raise_while_closed()

        return self._raw_audio_data

    @property
    def cipher(self):
        """解密音频数据所需的密码实例。"""
        return self._cipher

    @cipher.setter
    def cipher(self, new_cipher: CipherTypeVar):
        self._raise_while_closed()

        if not isinstance(new_cipher, (StreamCipher, BlockCipher)):
            raise TypeError(
                "attribute 'cipher' must be an instance of StreamCipher "
                f"or BlockCipher, not {type(new_cipher).__name__}"
            )
        self._cipher = new_cipher

    def tell(self) -> int:
        """返回当前流的操作位置。"""
        self._raise_while_closed()

        return self._offset

    def seek(self, offset: int, whence: int = 0, /) -> int:
        """改变流的操作位置为 `offset`。`offset` 将会相对于 `whence` 指定的位置进行转换。
        随后返回新的绝对位置。

        `whence` 的可用值有：
            0 - 缓冲流的开头（默认值）；`offset` 应大于等于 0。

            1 - 当前流的操作位置；`offset` 可以小于 0。

            2 - 缓冲流的末尾；`offset` 应当小于 0。"""
        self._raise_while_closed()

        if whence == 0:
            if offset < 0:
                raise ValueError(f'negative seek value {offset}')
            pos: int = offset
        elif whence == 1:
            if offset + self._offset < 0:
                pos: int = 0
            else:
                pos: int = offset + self._offset
        elif whence == 2:
            if offset + self._audio_length < 0:
                pos: int = 0
            else:
                pos: int = offset + self._audio_length
        else:
            raise ValueError(f'invalid whence ({whence}, should be 0, 1 or 2)')

        self._offset = pos
        return self.tell()

    def seekable(self) -> bool:
        """如果缓冲流支持从任意位置开始读取，返回 `True`。

        这个方法的存在是为了兼容性考虑，其总是返回 `True`。"""
        self._raise_while_closed()

        return True

    def read(self, size: int = -1, /) -> bytes:
        """读取、解密并返回缓冲区中最多 `size` 个字节。如果此参数被省略、为 `None` 或小于 0，
        则从当前流的操作位置开始，读取、解密并返回直到缓冲区末尾的所有数据。

        注意：受 `cipher` 属性指向的密码的影响，返回的数据大小可能不等于 `size`。"""
        self._raise_while_closed()

        if self._offset >= self._audio_length:
            return b''

        offset: int = self._offset
        if (size < -1) or (size > self._audio_length - self._offset):
            size: int = self._audio_length - self._offset
        else:
            size: int = size
        self._offset += size

        return self._cipher.decrypt(
            src=self._raw_audio_data[offset: offset + size],
            offset=offset
        )

    def read1(self, size: int = -1, /) -> bytes:
        """这个方法的存在是为了兼容性考虑，其行为与 `read()` 相同。"""
        self._raise_while_closed()

        return self.read(size)

    def readable(self) -> bool:
        """如果可以读取流，返回 `True`。

        这个方法的存在是为了兼容性考虑，其总是返回 `True`。"""
        self._raise_while_closed()

        return True

    def readinto(self, buffer: WritableBuffer, /) -> int:
        """将字节数据读入预先分配的、可写的类似字节的对象 `buffer`（例如，bytearray）中，
        并返回所读取的字节数。"""
        self._raise_while_closed()

        if not isinstance(buffer, WritableBuffer_tuple):
            raise TypeError(f'readinto() argument must be read-write bytes-like object, not {type(buffer).__name__}')
        buf_len: int = len(buffer)
        data: bytes = self.read(buf_len)
        data_len: int = len(data)

        if buf_len > data_len:
            buffer[:data_len] = data
        else:
            buffer[:] = data

        return data_len

    def readinto1(self, buffer: WritableBuffer, /) -> int:
        """这个方法的存在是为了兼容性考虑，其行为与 `readinto()` 相同。"""
        self._raise_while_closed()

        return self.readinto(buffer)

    def close(self) -> None:
        """关闭这个解码器及其包含的流。如果已经关闭，则此方法不会生效。

        解码器关闭后，除了对 `cipher` 属性的访问之外，任何操作都会引发 `ValueError`。

        为方便起见，允许多次调用此方法。但是，只有第一个调用才会生效。"""
        if not self.closed:
            del self._raw_audio_data

    @property
    def closed(self) -> bool:
        """如果解码器已经关闭，返回 True。"""
        return not hasattr(self, '_raw_audio_data')

    def _raise_while_closed(self):
        if not hasattr(self, '_raw_audio_data'):
            raise ValueError('I/O operation on closed Decoder.')

    @property
    def name(self) -> Optional[str]:
        return self._filename if self._filename else None

    def __repr__(self):
        ret = f"<{self.__class__.__name__} at {hex(id(self))}"
        if self.name:
            ret += f" name='{self.name}'"
        ret += '>'
        return ret
