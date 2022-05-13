from __future__ import annotations

from typing import Generator

from ._common import Cipher
from . import utils


class NCMRC4Cipher(Cipher):
    def __init__(self, key: bytes) -> None:
        super().__init__(key)

        # 使用 RC4-KSA 生成 S-box
        S = bytearray(range(256))
        j = 0
        key_len = len(key)
        for i in range(256):
            j = (j + S[i] + key[i % key_len]) & 0xff
            S[i], S[j] = S[j], S[i]

        # 使用 PRGA 从 S-box 生成密钥流
        stream_short = bytearray(256)
        for i in range(256):
            _ = (i + 1) & 0xff
            si = S[_] & 0xff
            sj = S[(_ + si) & 0xff] & 0xff
            stream_short[i] = S[(si + sj) & 0xff]

        self._keystream_short = stream_short

    def yield_keystream(self, src_len: int, offset: int) -> Generator[int, None, None]:
        keystream_short = self._keystream_short

        for i in range(offset, offset + src_len):
            yield keystream_short[i & 0xff]

    def decrypt(self, cipherdata: bytes, start_offset: int = 0) -> bytes:
        cipherdata_len = len(cipherdata)
        return utils.bytesxor(cipherdata, bytes(self.yield_keystream(cipherdata_len, start_offset)))
