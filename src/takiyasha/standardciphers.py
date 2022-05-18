from __future__ import annotations

from functools import partial
from io import BytesIO
from typing import Generator

from pyaes import AESModeOfOperationECB
from pyaes.util import append_PKCS7_padding, strip_PKCS7_padding

from .common import Cipher

__all__ = ['AES_MODE_ECB', 'TEA']


class AES_MODE_ECB(Cipher):
    @staticmethod
    def cipher_name() -> str:
        return 'AES (Mode ECB)'

    def __init__(self, key) -> None:
        super().__init__(key)

        self._raw_cipher = AESModeOfOperationECB(key=self._key)

    @property
    def raw_cipher(self) -> AESModeOfOperationECB:
        return self._raw_cipher

    @property
    def blocksize(self):
        return 16

    @property
    def support_offset(self) -> bool:
        return False

    def yield_block(self, data: bytes) -> Generator[bytes, None, None]:
        for blk in iter(partial(BytesIO(data).read, self.blocksize), b''):
            yield blk

    def decrypt(self, cipherdata: bytes, start_offset: int = 0) -> bytes:
        return strip_PKCS7_padding(
            b''.join(self._raw_cipher.decrypt(b) for b in self.yield_block(cipherdata))
        )

    def encrypt(self, plaindata: bytes, start_offset: int = 0) -> bytes:
        return b''.join(
            self._raw_cipher.encrypt(b) for b in self.yield_block(append_PKCS7_padding(plaindata))
        )


class TEA(Cipher):
    @staticmethod
    def cipher_name() -> str:
        return 'TEA'

    def __init__(self, key: bytes, rounds: int = 64, magic_number: int = 0x9e3779b9) -> None:
        if len(key) != self.blocksize():
            raise ValueError(f"incorrect key length {len(key)} (should be {self.blocksize()})")
        # if rounds & 1 != 0:
        if rounds % 2 != 0:
            raise ValueError(f'even number of rounds required (got {rounds})')

        super().__init__(key)
        self._rounds = rounds
        self._delta = magic_number

    @staticmethod
    def blocksize() -> int:
        return 16

    @property
    def support_offset(self) -> bool:
        return False

    @classmethod
    def transvalues(cls, data: bytes, key: bytes) -> tuple[int, int, int, int, int, int]:
        v0 = int.from_bytes(data[:4], 'big')
        v1 = int.from_bytes(data[4:8], 'big')
        k0 = int.from_bytes(key[:4], 'big')
        k1 = int.from_bytes(key[4:8], 'big')
        k2 = int.from_bytes(key[8:12], 'big')
        k3 = int.from_bytes(key[12:], 'big')

        return v0, v1, k0, k1, k2, k3

    def decrypt(self, cipherdata: bytes, start_offset: int = 0) -> bytes:
        v0, v1, k0, k1, k2, k3 = self.transvalues(cipherdata, self._key)

        delta = self._delta
        rounds = self._rounds
        ciphersum = (delta * (rounds // 2)) & 0xffffffff

        for i in range(rounds // 2):
            v1 -= ((v0 << 4) + k2) ^ (v0 + ciphersum) ^ ((v0 >> 5) + k3)
            v1 &= 0xffffffff
            v0 -= ((v1 << 4) + k0) ^ (v1 + ciphersum) ^ ((v1 >> 5) + k1)
            v0 &= 0xffffffff
            ciphersum -= delta
            ciphersum &= 0xffffffff

        return v0.to_bytes(4, 'big') + v1.to_bytes(4, 'big')

    def encrypt(self, plaindata: bytes, start_offset: int = 0) -> bytes:
        v0, v1, k0, k1, k2, k3 = self.transvalues(plaindata, self._key)

        delta = self._delta
        rounds = self._rounds
        ciphersum = 0

        for i in range(rounds // 2):
            ciphersum += delta
            ciphersum &= 0xffffffff
            v0 += ((v1 << 4) + k0) ^ (v1 + ciphersum) ^ ((v1 >> 5) + k1)
            v0 &= 0xffffffff
            v1 += ((v0 << 4) + k2) ^ (v0 + ciphersum) ^ ((v0 >> 5) + k3)
            v1 &= 0xffffffff

        return v0.to_bytes(4, 'big') + v1.to_bytes(4, 'big')
