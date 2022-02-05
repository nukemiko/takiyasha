from typing import Optional

from ..common import StreamCipher


class TM_Cipher(StreamCipher):
    def __init__(self, key: Optional[bytes] = None):
        super().__init__(key)

    def decrypt(self, src: bytes, offset: int = 0) -> bytes:
        m4a_header: bytes = b'\x00\x00\x00\x1cftyp'
        if offset > 8:
            return bytes(src)
        else:
            data_len: int = len(src)
            if data_len <= 8 - offset:
                data: bytes = m4a_header[offset:data_len]
            else:
                data: bytes = src.replace(src[:8 - offset], m4a_header[offset:])

            return data
