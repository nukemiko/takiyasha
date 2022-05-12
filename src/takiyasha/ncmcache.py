from __future__ import annotations

from ._common import CryptedIOBase, KeylessCipher


class NcmCacheCipher(KeylessCipher):
    def decrypt(self, cipherdata: bytes, start_offset: int = 0) -> bytes:
        bool(start_offset)
        return bytes(b ^ 163 for b in cipherdata)


class NcmCacheCryptedIO(CryptedIOBase):
    def __init__(self, initial_bytes: bytes | bytearray = b'') -> None:
        super().__init__(initial_bytes)
        self._cipher = NcmCacheCipher()
