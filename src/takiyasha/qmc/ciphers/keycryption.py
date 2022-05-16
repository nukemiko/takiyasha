from __future__ import annotations

from base64 import b64decode

from ...common import KeylessCipher
from ...exceptions import DecryptException, InvalidDataError
from ...standardciphers import TEA
from ...utils import bytesxor


class ValidationError(DecryptException):
    pass


class QMCv2Key(KeylessCipher):
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
            dest_buf[:] = tea_blk.decrypt(bytesxor(dest_buf[:8], iv_current[:8]))
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
