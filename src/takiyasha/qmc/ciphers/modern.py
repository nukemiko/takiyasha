from __future__ import annotations

import os

from ...common import Cipher, KeylessCipher
from ...utils import bytesxor

QMCv1_KEYSTREAM_1ST_SEGMENT = b''
QMCv1_KEYSTREAM_REMAINING_SEGMENT = b''


def load_segment_file() -> None:
    global QMCv1_KEYSTREAM_1ST_SEGMENT, QMCv1_KEYSTREAM_REMAINING_SEGMENT
    if not (QMCv1_KEYSTREAM_1ST_SEGMENT and QMCv1_KEYSTREAM_REMAINING_SEGMENT):
        with open(os.path.join(os.path.dirname(__file__), '../binary/QMCv1-keystream-segment'), 'rb') as seg_file:
            QMCv1_KEYSTREAM_1ST_SEGMENT = seg_file.read(32768)
            QMCv1_KEYSTREAM_REMAINING_SEGMENT = seg_file.read(32767)


class StaticMap(KeylessCipher):
    def __init__(self):
        load_segment_file()

    def decrypt(self, cipherdata: bytes, start_offset: int = 0) -> bytes:
        firstseg = QMCv1_KEYSTREAM_1ST_SEGMENT
        otherseg = QMCv1_KEYSTREAM_REMAINING_SEGMENT

        if 0 <= start_offset <= len(firstseg):
            start_segend_len = len(firstseg) - start_offset
            if len(cipherdata) <= start_segend_len:
                keystream = firstseg[start_offset:start_offset + len(cipherdata)]
            else:
                srcseg2 = cipherdata[start_segend_len:]
                srcseg2_len = len(srcseg2)
                stream1 = otherseg[start_offset:]
                stream2 = otherseg * (srcseg2_len // len(otherseg)) + otherseg[:srcseg2_len % len(otherseg)]
                keystream = stream1 + stream2
        else:
            start_in_seg_pos = (start_offset - len(firstseg)) % len(otherseg)
            start_segend_len = len(otherseg) - start_in_seg_pos
            if len(cipherdata) <= start_segend_len:
                keystream = otherseg[start_in_seg_pos:start_in_seg_pos + len(cipherdata)]
            else:
                srcseg2 = cipherdata[start_segend_len:]
                srcseg2_len = len(srcseg2)
                stream1 = otherseg[start_in_seg_pos:]
                stream2 = otherseg * (srcseg2_len // len(otherseg)) + otherseg[:srcseg2_len % len(otherseg)]
                keystream = stream1 + stream2

        return bytesxor(cipherdata, keystream)


class DynamicMap(Cipher):
    def yield_mask(self, data: bytes, offset: int):
        key: bytes = self._key
        key_len = len(key)

        for i in range(offset, offset + len(data)):
            if i > 0x7fff:
                i %= 0x7fff
            idx = (i ** 2 + 71214) % key_len

            value = key[idx]
            rotate = ((idx & 7) + 4) % 8

            yield ((value << rotate) % 256) | ((value >> rotate) % 256)

    def decrypt(self, cipherdata: bytes, start_offset: int = 0) -> bytes:
        keystream = bytes(self.yield_mask(cipherdata, start_offset))
        return bytesxor(cipherdata, keystream)
