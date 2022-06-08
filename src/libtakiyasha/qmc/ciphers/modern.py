from __future__ import annotations

import os
from typing import Generator

from ...common import Cipher, KeylessCipher
from ...utils import bytesxor

QMCv1_KEYSTREAM_1ST_SEGMENT = b''
QMCv1_KEYSTREAM_REMAINING_SEGMENT = b''

__all__ = ['DynamicMap', 'ModifiedRC4', 'StaticMap']


def load_segment_file() -> None:
    global QMCv1_KEYSTREAM_1ST_SEGMENT, QMCv1_KEYSTREAM_REMAINING_SEGMENT
    if not (QMCv1_KEYSTREAM_1ST_SEGMENT and QMCv1_KEYSTREAM_REMAINING_SEGMENT):
        with open(os.path.join(os.path.dirname(__file__), 'binaries/QMCv1-keystream-segment'), 'rb') as seg_file:
            QMCv1_KEYSTREAM_1ST_SEGMENT = seg_file.read(32768)
            QMCv1_KEYSTREAM_REMAINING_SEGMENT = seg_file.read(32767)


class StaticMap(KeylessCipher):
    @staticmethod
    def cipher_name() -> str:
        return 'Static Mapping'

    def __init__(self):
        load_segment_file()

    def decrypt(self, cipherdata: bytes, start_offset: int = 0) -> bytes:
        first_seg = QMCv1_KEYSTREAM_1ST_SEGMENT
        remain_seg = QMCv1_KEYSTREAM_REMAINING_SEGMENT
        first_seg_len = len(first_seg)
        remain_seg_len = len(remain_seg)

        end_offset = start_offset + len(cipherdata)

        if start_offset < 0:
            raise ValueError("'start_offset' must be a positive integer")
        else:
            data = cipherdata.rjust(end_offset, b'\x00')
            data_len = len(data)
            if data_len <= first_seg_len:
                return bytesxor(data[start_offset:], first_seg[start_offset:end_offset])
            else:
                remain_data_len = data_len - first_seg_len
                required_remain_seg_count = remain_data_len // remain_seg_len
                if remain_data_len % remain_seg_len != 0:
                    required_remain_seg_count += 1
                keystream = first_seg + remain_seg * required_remain_seg_count
                return bytesxor(data[start_offset:], keystream[start_offset:end_offset])


class DynamicMap(Cipher):
    @staticmethod
    def cipher_name() -> str:
        return 'Dynamic Mapping'

    def yield_mask(self, data_offset: int, data_len: int):
        key: bytes = self._key
        key_len = len(key)

        for i in range(data_offset, data_offset + data_len):
            if i > 0x7fff:
                i %= 0x7fff
            idx = (i ** 2 + 71214) % key_len

            value = key[idx]
            rotate = ((idx & 7) + 4) % 8

            yield ((value << rotate) % 256) | ((value >> rotate) % 256)

    def decrypt(self, cipherdata: bytes, start_offset: int = 0) -> bytes:
        keystream = bytes(self.yield_mask(start_offset, len(cipherdata)))
        return bytesxor(cipherdata, keystream)


class ModifiedRC4(Cipher):
    @staticmethod
    def cipher_name() -> str:
        return 'Modified RC4'

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

    def decrypt(self, cipherdata: bytes, start_offset: int = 0) -> bytes:
        first_segsize = self.first_segsize()
        remain_segsize = self.remain_segsize()
        gen_remain_seg = self.gen_remain_seg

        pending = len(cipherdata)
        done = 0
        offset = int(start_offset)
        keystream_buffer = bytearray(pending)

        def mark(p: int) -> None:
            nonlocal pending, done, offset

            pending -= p
            done += p
            offset += p

        if 0 <= offset < first_segsize:
            blksize = pending
            if blksize > first_segsize - offset:
                blksize = first_segsize - offset
            keystream_buffer[:blksize] = self.gen_first_seg(offset, blksize)
            mark(blksize)
            if pending <= 0:
                return bytesxor(cipherdata, keystream_buffer)

        if offset % remain_segsize != 0:
            blksize = pending
            if blksize > remain_segsize - (offset % remain_segsize):
                blksize = remain_segsize - (offset % remain_segsize)
            keystream_buffer[done:done + blksize] = gen_remain_seg(offset, blksize)
            mark(blksize)
            if pending <= 0:
                return bytesxor(cipherdata, keystream_buffer)

        while pending > remain_segsize:
            keystream_buffer[done:done + remain_segsize] = gen_remain_seg(offset, remain_segsize)
            mark(remain_segsize)

        if pending > 0:
            keystream_buffer[done:] = gen_remain_seg(offset, len(keystream_buffer[done:]))

        return bytesxor(cipherdata, keystream_buffer)
