from __future__ import annotations

from io import BytesIO, IOBase, UnsupportedOperation
from typing import Union


class KeylessCipher:
    @property
    def support_offset(self):
        return True

    @property
    def support_decrypt(self) -> bool:
        return True

    def decrypt(self, cipherdata: bytes, start_offset: int = 0) -> bytes:
        bool(start_offset)
        return bytes(cipherdata)

    @property
    def support_encrypt(self) -> bool:
        return True

    def encrypt(self, plaindata: bytes, start_offset: int = 0) -> bytes:
        return self.decrypt(cipherdata=plaindata, start_offset=start_offset)


class Cipher(KeylessCipher):
    def __init__(self, key: bytes) -> None:
        if not isinstance(key, bytes):
            self._key = bytes(key)
        else:
            self._key = key

    @property
    def key(self) -> bytes:
        return self._key


Ciphers = Union[KeylessCipher, Cipher]


class CryptedIOBase(IOBase):
    def __init__(self, initial_bytes: bytes | bytearray) -> None:
        self._raw = BytesIO(initial_bytes)
        self._cipher = KeylessCipher()

    @property
    def raw(self):
        return self._raw

    @property
    def cipher(self) -> Ciphers:
        return self._cipher

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
