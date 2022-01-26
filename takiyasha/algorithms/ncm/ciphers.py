from typing import Generator

from ..common import Cipher, StreamCipher
from ...typehints import BytesType, BytesType_tuple
from ...utils import xor_bytestrings


class NCM_RC4Cipher(Cipher):
    """A cipher that implemented decryption of the NCM encrypted container format.
    
    If the first 8 bytes of the file is equal to bytestring "CTENFDAM", this cipher should be used."""

    def __init__(self, key: BytesType):
        if key is None:
            raise TypeError(f"'key' must be byte or bytearray, not None")
        super().__init__(key)

        # build S-box
        box: bytearray = bytearray(range(256))
        j: int = 0
        for i in range(256):
            j = (j + box[i] + self.key[i % self.key_length]) & 0xff
            box[i], box[j] = box[j], box[i]

        final_box: bytearray = bytearray(256)
        for i in range(256):
            _: int = (i + 1) & 0xff
            si: int = box[_] & 0xff
            sj: int = box[(_ + si) & 0xff] & 0xff
            final_box[i] = box[(si + sj) & 0xff]

        self._box: bytearray = final_box

    @property
    def box(self):
        return self._box

    def decrypt(self, src_data: BytesType, /, offset: int = 0) -> bytes:
        src_data_len: int = len(src_data)
        return bytes(self.box[(offset + i) & 0xff] ^ src_data[i] for i in range(src_data_len))


class NCM_XOROnlyCipher(Cipher):
    """A cipher that implemented decryption of the Cloudmusic encrypted and cached music file.
    
    If the file format is not recognized and the file does not begin with the byte string "CTENFDAM",
    but you are sure it was downloaded from Cloudmusic, this cipher should be used."""

    def __init__(self):
        super().__init__(key=None)

    def decrypt(self, src_data: BytesType, /, offset: int = 0) -> bytes:
        return bytes(b ^ 163 for b in src_data)


class NCM_NewRC4Cipher(StreamCipher):
    def __init__(self, key: BytesType):
        if not isinstance(key, BytesType_tuple):
            raise TypeError(f"'key' must be bytes or bytearray, not {type(key).__name__}")
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
        # stream: bytes = bytes(box[(offset + i) & 0xff] for i in range(len(src)))
        stream: bytes = bytes(self._yield_stream(len(src), offset))
        return xor_bytestrings(stream, src)


class NCM_NewXORCipher(StreamCipher):
    def __init__(self, key: BytesType = None):
        super().__init__(key)

    def decrypt(self, src: bytes, offset: int = 0) -> bytes:
        stream: bytes = bytes([163]) * len(src)
        return xor_bytestrings(stream, src)
