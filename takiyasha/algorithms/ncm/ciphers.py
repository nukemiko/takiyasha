from ..common import Cipher
from ...typehints import BytesType


class RC4Cipher(Cipher):
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
    
    def decrypt(self, src_data: BytesType, /, offset: int = 0) -> bytes:
        src_data_len: int = len(src_data)
        return bytes(self._box[(offset + i) & 0xff] ^ src_data[i] for i in range(src_data_len))


class CacheCipher(Cipher):
    def __init__(self):
        super().__init__(key=None)
    
    def decrypt(self, src_data: BytesType, /) -> bytes:
        return bytes(b ^ 163 for b in src_data)
