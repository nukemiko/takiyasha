from __future__ import annotations

from base64 import b64decode
from typing import IO

from . import legacyconstants
from .legacy import Key256Mask128
from ... import utils
from ...common import KeylessCipher
from ...exceptions import DecryptException, InvalidDataError
from ...standardciphers import TEA

__all__ = ['find_mflac_mask', 'find_mgg_mask', 'QMCv2Key', 'ValidationError']


class ValidationError(DecryptException):
    pass


class QMCv2Key(KeylessCipher):
    @staticmethod
    def cipher_name() -> str:
        return 'TEA (Mode ECB) Based Block Cipher'

    @property
    def support_offset(self) -> bool:
        return False

    @property
    def support_encrypt(self) -> bool:
        return False

    @staticmethod
    def salt_len() -> int:
        return 2

    @staticmethod
    def zero_len() -> int:
        return 7

    @staticmethod
    def simple_key() -> bytes:
        """此处直接返回预先计算好的密钥，计算方法如下：

        >>> from math import tan
        >>> salt: int = 106
        >>> length: int = 8
        >>> # 以下是计算的过程和结果（储存在 key_buf 中）
        >>> key_buf: bytearray = bytearray(length)
        >>> for i in range(length):
        ...     tan_result = tan(salt + i * 0.1)
        ...     key_buf[i] = int(abs(tan_result * 100))
        """
        return b'\x69\x56\x46\x38\x2b\x20\x15\x0b'

    @classmethod
    def tea_recipe2key(cls, recipe: bytes) -> bytes:
        simple_key = cls.simple_key()
        tea_key_buf = bytearray(16)
        for i in range(8):
            tea_key_buf[i << 1] = simple_key[i]
            tea_key_buf[(i << 1) + 1] = recipe[i]

        return bytes(tea_key_buf)

    @classmethod
    def decrypt_tencent_tea(cls,
                            encrypted_keydata: bytes,
                            tea_key: bytes,
                            # skip_zero_check: bool = False
                            ) -> bytes:
        salt_len: int = cls.salt_len()
        zero_len: int = cls.zero_len()

        in_buf = bytearray(encrypted_keydata)
        if len(in_buf) % 8 != 0:
            raise ValueError(f"encrypted key size ({len(in_buf)}) "
                             f"is not a multiple of the block size ({TEA.blocksize()})"
                             )
        if len(in_buf) < 16:
            raise ValueError(f"encrypted keydata length is too short "
                             f"(should be >= 16, got {len(in_buf)})"
                             )
        tea_blk = TEA(tea_key, rounds=32)

        dest_buf = bytearray(tea_blk.decrypt(in_buf))
        pad_len = dest_buf[0] & 0x7
        out_buf_len = len(in_buf) - pad_len - salt_len - zero_len - 1
        if pad_len + salt_len != 8:
            raise InvalidDataError(f'invalid pad length {pad_len}')
        out_buf = bytearray(out_buf_len)

        iv_previous = bytearray(8)
        iv_current = in_buf[:8]

        in_buf_pos = 8

        dest_idx = 1 + pad_len

        def crypt_block() -> None:
            nonlocal in_buf_pos
            iv_previous[:] = iv_current[:]
            iv_current[:] = in_buf[in_buf_pos:in_buf_pos + 8]
            dest_buf[:] = tea_blk.decrypt(utils.bytesxor(dest_buf[:8], iv_current[:8]))
            in_buf_pos += 8

        i = 1
        while i <= salt_len:
            if dest_idx < 8:
                dest_idx += 1
                i += 1
            elif dest_idx == 8:
                crypt_block()
                dest_idx = 0

        out_buf_pos = 0
        while out_buf_pos < out_buf_len:
            if dest_idx < 8:
                out_buf[out_buf_pos] = dest_buf[dest_idx] ^ iv_previous[dest_idx]
                dest_idx += 1
                out_buf_pos += 1
            elif dest_idx == 8:
                crypt_block()
                dest_idx = 0

        # 这一段循环可能是多余的，因为其只是把两串数组的同一位置的值对比了 zero_len - 1 次
        # for i in range(1, zero_len):
        #     if dest_buf[dest_idx] != iv_previous[dest_idx]:
        #         raise ValidationError('zero check failed')
        # if not skip_zero_check:
        #     if dest_buf[dest_idx] != iv_previous[dest_idx]:
        #         raise ValidationError('zero check failed')

        return bytes(out_buf)

    def decrypt(self, cipherdata: bytes, start_offset: int = 0) -> bytes:
        decoded_cipherdata = b64decode(cipherdata, validate=True)
        if len(decoded_cipherdata) < 16:
            raise ValueError('cipherdata length is too short '
                             f'(should be >= 16, got {len(decoded_cipherdata)}'
                             )
        tea_key_recipe = decoded_cipherdata[:8]
        encrypted_keydata = decoded_cipherdata[8:]

        tea_key = self.tea_recipe2key(tea_key_recipe)

        rs = self.decrypt_tencent_tea(encrypted_keydata, tea_key)

        return tea_key_recipe + rs

    def encrypt(self, plaindata: bytes, start_offset: int = 0) -> bytes:
        raise NotImplementedError


def find_mflac_mask(fileobj: IO[bytes]) -> bytes | None:
    utils.verify_fileobj_readable(fileobj)
    utils.verify_fileobj_seekable(fileobj)

    data_len = fileobj.seek(0, 2)
    test_len = min(0x8000, data_len)
    fileobj.seek(0, 0)
    file_header = fileobj.read(4)
    fileobj.seek(0, 0)

    while fileobj.tell() <= test_len:  # 这里的 tell() 返回 read() 之后的位置
        data_offset = fileobj.tell()  # 这里的 tell() 返回 read() 之前的位置（mask 的位置）
        mask = fileobj.read(128)
        stream = bytes(Key256Mask128.yield_mask(mask, data_offset, 4))
        if utils.bytesxor(file_header, stream) == b'fLaC':
            return mask


def find_mgg_mask(fileobj: IO[bytes]) -> bytes | None:
    utils.verify_fileobj_readable(fileobj)
    utils.verify_fileobj_seekable(fileobj)
    fileobj.seek(0, 0)
    data = fileobj.read()

    if len(data) < 0x100:
        raise ValueError(f"data length should be greater than {0x100}, got {len(data)}")

    mask_confidence: list[dict[int, int]] = [{} for _ in range(44)]

    page2_size = data[0x54] ^ data[0xc] ^ legacyconstants.ogg_public_header1[0xc]
    spec_header, spec_confidence = generate_ogg_full_header(page2_size)
    test_len = len(spec_header)

    for idx128 in range(test_len):
        confidence = spec_confidence[idx128]
        if confidence > 0:
            tempmask = data[idx128] ^ spec_header[idx128]

            idx44 = legacyconstants.key256mapping_128to44[idx128 & 0x7f]
            if mask_confidence[idx44].get(tempmask):
                mask_confidence[idx44][tempmask] += confidence
            else:
                mask_confidence[idx44][tempmask] = confidence

    mask = bytearray(44)
    for i in range(44):
        mask[i] = decide_mgg_mask256_item_conf(mask_confidence[i])

    cipher = Key256Mask128(mask)
    if cipher.decrypt(data[:4], 0).startswith(b'OggS'):
        return bytes(mask)


def generate_ogg_full_header(page_size: int) -> tuple[bytes, list[int]]:
    spec = bytearray(page_size + 1)
    spec[0], spec[1], spec[page_size] = page_size & 0xff, 0xff, 0xff
    for i in range(2, page_size):
        spec[i] = 0xff
    spec_confidence: list[int] = [0] * (page_size + 1)
    spec_confidence[0], spec_confidence[1], spec_confidence[page_size] = 6, 0, 0
    for i in range(2, page_size):
        spec_confidence[i] = 4

    all_confidence = legacyconstants.ogg_public_confidence1[:] + spec_confidence + legacyconstants.ogg_public_confidence2[:]
    all_header = b''.join([legacyconstants.ogg_public_header1, spec, legacyconstants.ogg_public_header2])

    return all_header, all_confidence


def decide_mgg_mask256_item_conf(confidence: dict[int, int]) -> int:
    conf_len = len(confidence)
    if conf_len == 0:
        raise ValueError("cannot match at least one key")
    elif conf_len > 1:
        # 2 potential value for the mask
        pass
    result, conf = 0, 0
    for idx, item in confidence.items():
        if item > conf:
            result = idx
            result &= 0xff
            conf = item

    return result
