from typing import Generator, Optional

from ..common import StreamCipher
from ...utils import xor_bytestrings


class NCM_RC4Cipher(StreamCipher):
    def __init__(self, key: bytes):
        if not isinstance(key, bytes):
            raise TypeError(f"'key' must be bytes, not {type(key).__name__}")
        super().__init__(bytes(key))

        first_box: bytearray = bytearray(range(256))
        j: int = 0
        for i in range(256):
            j = (j + first_box[i] + self.key[i % self.key_length]) & 0xff
            first_box[i], first_box[j] = first_box[j], first_box[i]

        final_box: bytearray = bytearray(256)
        for i in range(256):
            _: int = (i + 1) & 0xff
            si: int = first_box[_] & 0xff
            sj: int = first_box[(_ + si) & 0xff] & 0xff
            final_box[i] = first_box[(si + sj) & 0xff]

        self._box: bytes = bytes(final_box)

    @property
    def box(self) -> bytes:
        return self._box

    def _yield_stream(self, buffer_len: int, offset: int) -> Generator[int, None, None]:
        box: bytes = self.box

        for i in range(offset, offset + buffer_len):
            yield box[i & 0xff]

    def decrypt(self, src: bytes, offset: int = 0) -> bytes:
        stream: bytes = bytes(self._yield_stream(len(src), offset))
        return xor_bytestrings(stream, src)


class NCM_XorOnlyCipher(StreamCipher):
    def __init__(self, key: Optional[bytes] = None):
        super().__init__(key)

    def decrypt(self, src: bytes, offset: int = 0) -> bytes:
        stream: bytes = bytes([163]) * len(src)
        return xor_bytestrings(stream, src)
