from __future__ import annotations

from io import BytesIO, IOBase, UnsupportedOperation
from typing import IO, Union

from . import utils

__all__ = ['Cipher', 'Ciphers', 'Crypter', 'KeylessCipher']


class KeylessCipher:
    @staticmethod
    def cipher_name() -> str:
        """Cipher 实现的名字。"""
        return 'No-op Keyless Cipher'

    @property
    def support_offset(self) -> bool:
        """指示 Cipher 实现是否可以根据源数据在文件中的位置，对源数据进行加/解密
        （即 ``encrypt``/``decrypt`` 方法的 ``start_offset`` 参数是否会影响其行为）。

        如果返回 False，说明 Cipher 实现不支持此特性，``start_offset`` 参数将被忽略。"""
        return True

    @property
    def support_decrypt(self) -> bool:
        """指示 Cipher 实现是否支持解密。"""
        return True

    def decrypt(self, cipherdata: bytes, start_offset: int = 0) -> bytes:
        bool(start_offset)
        return bytes(cipherdata)

    @property
    def support_encrypt(self) -> bool:
        """指示 Cipher 实现是否支持加密。"""
        return True

    def encrypt(self, plaindata: bytes, start_offset: int = 0) -> bytes:
        return self.decrypt(cipherdata=plaindata, start_offset=start_offset)


class Cipher(KeylessCipher):
    def __init__(self, key: bytes) -> None:
        if not isinstance(key, bytes):
            self._key = bytes(key)
        else:
            self._key = key

    @staticmethod
    def cipher_name() -> str:
        return 'No-op Cipher'

    @property
    def key(self) -> bytes:
        return self._key


Ciphers = Union[KeylessCipher, Cipher]


class Crypter(IOBase, IO[bytes]):
    def __init__(self, filething: utils.FileThing | None = None, **kwargs) -> None:
        if filething is None:
            self._raw = BytesIO()
            self._cipher: Ciphers = KeylessCipher()
            self._name: str | None = None
        else:
            self.load(filething, **kwargs)

    def load(self, filething: utils.FileThing, **kwargs) -> None:
        if utils.is_filepath(filething):
            fileobj: IO[bytes] = open(filething, 'rb')  # type: ignore
            self._name: str | None = fileobj.name
        else:
            fileobj: IO[bytes] = filething  # type: ignore
            self._name: str | None = getattr(fileobj, 'name', None)
            utils.verify_fileobj_readable(fileobj, bytes)
            utils.verify_fileobj_seekable(fileobj)

        fileobj.seek(0, 0)
        self._raw = BytesIO(fileobj.read())
        if utils.is_filepath(filething):
            fileobj.close()
        self._cipher: Ciphers = KeylessCipher()

    def save(self, filething: utils.FileThing | None = None, **kwargs) -> None:
        if filething:
            if utils.is_filepath(filething):
                fileobj: IO[bytes] = open(filething, 'wb')  # type: ignore
            else:
                fileobj: IO[bytes] = filething  # type: ignore
                utils.verify_fileobj_writable(fileobj, bytes)
        elif self._name:
            fileobj: IO[bytes] = open(self._name, 'wb')
        else:
            raise ValueError('missing filepath or fileobj')

        self._raw.seek(0, 0)
        fileobj.write(self._raw.read())
        if utils.is_filepath(filething):
            fileobj.close()

    @property
    def raw(self):
        return self._raw

    @property
    def cipher(self) -> Ciphers:
        return self._cipher

    @property
    def name(self) -> str | None:
        return self._name

    def close(self) -> None:
        self._raw.close()

    @property
    def closed(self) -> bool:
        return self._raw.closed

    def flush(self) -> None:
        self._raw.flush()

    def seekable(self) -> bool:
        return self._raw.seekable() and self._cipher.support_offset

    def seek(self, offset: int, whence: int = 0, /) -> int:
        if not self.seekable():
            raise UnsupportedOperation('seek')

        return self._raw.seek(offset, whence)

    def tell(self) -> int:
        if not self.seekable():
            raise UnsupportedOperation('tell')

        return self._raw.tell()

    def truncate(self, size: int | None = None, /) -> int:
        if not self.seekable():
            raise UnsupportedOperation('truncate')

        return self._raw.truncate(size)

    def readable(self) -> bool:
        return self._raw.readable() and self._cipher.support_decrypt

    def read(self, size: int = -1, /) -> bytes:
        if not self.readable():
            raise UnsupportedOperation('read')

        curpos = self.tell() if self.seekable() else 0
        return self._cipher.decrypt(self._raw.read(size), curpos)

    def writable(self) -> bool:
        return self._raw.writable() and self._cipher.support_encrypt

    def write(self, data: bytes | bytearray, /) -> int:
        if not self.writable():
            raise UnsupportedOperation('write')

        curpos = self.tell() if self.seekable() else 0
        return self._raw.write(self._cipher.encrypt(data, curpos))

    def __repr__(self) -> str:
        self_cls_name: str = type(self).__name__
        file_name: str | None = self._name
        ret = f"<{self_cls_name}"
        if self_cls_name != 'Crypter':
            ret += ' file, '
        if file_name is None:
            ret += f'at {hex(id(self))}'
        else:
            ret += f'name={repr(file_name)}'
        ret += '>'

        return ret
