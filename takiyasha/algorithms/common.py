from abc import ABCMeta, abstractmethod
from io import BufferedIOBase, BytesIO, DEFAULT_BUFFER_SIZE
from typing import BinaryIO, IO, Optional, TypeVar, Union

from ..typehints import (
    BytesType,
    PathType,
    WritableBuffer,
    WritableBuffer_tuple
)
from ..utils import (
    get_file_name_from_fileobj,
    is_fileobj,
    raise_while_not_fileobj
)


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

    def __repr__(self):
        return f'{type(self).__name__}(key={self.key})'

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


Cipher = TypeVar('Cipher', StreamCipher, BlockCipher)
"""用于表示 StreamCipher 和 BlockCipher，以及继承自两者的子类的类型变量。"""


class Decoder(BufferedIOBase, BinaryIO, metaclass=ABCMeta):
    """为构建一个解码器提供的基础层次结构。

    这个基类实现了一个只读且可从任意位置读取的缓冲二进制流，使用加密的音频数据作为缓冲区，
    在读取时返回解密的数据。"""

    @classmethod
    def from_file(cls, filething: Union[PathType, IO[bytes]]):
        """从一个文件或文件对象中读取数据，创建并返回一个新的解码器实例。

        Args:
            filething: 文件路径或文件对象。
                       若为路径，指向的必须是可读取的文件；
                       若为文件对象，必须可读取且支持从任意位置读取。
        Returns:
            新的解码器实例"""
        if is_fileobj(filething):
            raise_while_not_fileobj(filething, seekable=True, readable=True)
            file: IO[bytes] = filething
        else:
            file: IO[bytes] = open(filething, 'rb')

        raw_audio_data, cipher, misc = cls._pre_create_instance(file)
        file_name: str = get_file_name_from_fileobj(file)

        return cls(raw_audio_data, cipher, misc, file_name)

    @classmethod
    def from_bytes(cls, src: BytesType):
        """使用 `src`中的数据，创建并返回一个新的解码器实例。

        Args:
            src: 需要解码的数据，可以为 bytes 或 bytearray。
        Returns:
            新的解码器实例"""
        raw_audio_data, cipher, misc = cls._pre_create_instance(BytesIO(src))
        file_name: str = ''

        return cls(raw_audio_data, cipher, misc, file_name)

    @classmethod
    @abstractmethod
    def _pre_create_instance(cls, file: IO[bytes]) -> tuple[bytes, Cipher, dict[str, ...]]:
        """从文件中获取并返回创建解码器实例所需的信息。

        没有这些信息就无法创建解码器实例，因此这是一个必须实现的抽象方法。

        Args:
            file: 文件对象
        Returns:
            一个包含了加密的音频数据、根据加密类型创建的密码实例，以及其他信息（例如元数据等）的元组。"""

    def __init__(
            self,
            raw_audio_data: bytes,
            cipher: Cipher,
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
        self._cipher: Cipher = cipher
        self._misc: dict[str, ...] = misc

        self._iter_blocksize: int = DEFAULT_BUFFER_SIZE

    def __iter__(self):
        return self

    def __next__(self):
        bytestring: bytes = self.read(self._iter_blocksize)
        if bytestring == b'':
            raise StopIteration

        return bytestring

    @property
    def iter_blocksize(self) -> int:
        """迭代解码器对象时，每次迭代所返回的字节大小。

        默认值由 `io.DEFAULT_BUFFER_SIZE` 决定，可以重新设置为一个非零正整数。"""
        return self._iter_blocksize

    @iter_blocksize.setter
    def iter_blocksize(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError(f"'{type(value).__name__}' object cannot be interpreted as an integer")
        if value <= 0:
            raise ValueError(f"a non-zero positive integer required (got {value})")

        self._iter_blocksize = value

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
    def cipher(self, new_cipher: Cipher):
        self._raise_while_closed()

        if not isinstance(new_cipher, (StreamCipher, BlockCipher)):
            raise TypeError(
                "attribute 'cipher' must be an instance of StreamCipher "
                f"or BlockCipher, not {type(new_cipher).__name__}"
            )
        self._cipher = new_cipher

    @property
    def audio_format(self) -> Optional[str]:
        """返回音频的格式。

        如果无法识别音频格式，或者其它解码器实现没有实现此行为，返回 `None`。"""
        return self._misc.get('audio_format')

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
        if (size <= -1) or (size > self._audio_length - self._offset):
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

    def _raise_while_closed(self) -> None:
        if not hasattr(self, '_raw_audio_data'):
            raise ValueError('I/O operation on closed Decoder')

    @property
    def name(self) -> Optional[str]:
        """作为解码器数据来源的文件名。若数据不是来源于文件，则为空。"""
        return self._filename if self._filename else None

    def __repr__(self):
        ret = f"<{self.__class__.__name__} at {hex(id(self))}"
        if self.name:
            ret += f" name='{self.name}'"
        ret += '>'
        return ret
