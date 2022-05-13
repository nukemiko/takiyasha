from __future__ import annotations

import os
from typing import Generator

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


class ModifiedRC4(Cipher):
    @staticmethod
    def first_segsize() -> int:
        return 128

    @staticmethod
    def remain_segsize() -> int:
        return 5120

    @staticmethod
    def get_hash_base(key: bytes) -> int:
        hash_base = 1
        key_len = len(key)

        for i in range(key_len):
            v: int = key[i]
            if v == 0:
                continue
            next_hash: int = (hash_base * v) & 0xffffffff
            if next_hash == 0 or next_hash <= hash_base:
                break
            hash_base = next_hash
        return hash_base

    def __init__(self, key: bytes):
        super().__init__(key)
        key_len = len(key)
        self._key_len = key_len

        box: bytearray = bytearray(i % 256 for i in range(key_len))

        j: int = 0
        for i in range(key_len):
            j = (j + box[i] + key[i % key_len]) % key_len
            box[i], box[j] = box[j], box[i]
        self._box: bytearray = box

        self._hash_base = self.get_hash_base(key)

    def get_seg_skip(self, v: int) -> int:
        key: bytes = self._key
        key_len: int = self._key_len
        hash_: int = self._hash_base

        seed: int = key[v % key_len]
        idx: int = int(hash_ / ((v + 1) * seed) * 100)

        return idx % key_len

    def gen_first_seg(self,
                      data_offset: int,
                      data_len: int
                      ) -> Generator[int, None, None]:
        key = self._key

        for i in range(data_offset, data_offset + data_len):
            yield key[self.get_seg_skip(i)]

    def gen_remain_seg(self,
                       data_offset: int,
                       data_len: int
                       ) -> Generator[int, None, None]:
        key_len = self._key_len
        box = self._box.copy()
        j, k = 0, 0

        skip_len = (data_offset % self.remain_segsize()) + self.get_seg_skip(data_offset // self.remain_segsize())
        for i in range(-skip_len, data_len):
            j = (j + 1) % key_len
            k = (box[j] + k) % key_len
            box[j], box[k] = box[k], box[j]
            if i >= 0:
                yield box[(box[j] + box[k]) % key_len]
