from base64 import b64decode
from math import tan
from typing import Final

from Cryptodome.Util.strxor import strxor

from .ciphers import TEACipher
from ...exceptions import DecryptionError
from ...typehints import BytesType


def simple_make_key(salt: int, length: int) -> bytearray:
    key: bytearray = bytearray(length)
    for i in range(length):
        key[i] = int(abs(tan(salt + i * 0.1)) * 100)
    return key


def xor_8bytes(term1: BytesType, term2: BytesType) -> bytearray:
    term1 = term1[:8]
    term2 = term2[:8]
    return bytearray(strxor(term1, term2))


def decrypt_tc_tea(input_data: BytesType, key: BytesType) -> bytearray:
    salt_len: Final[int] = 2
    zero_len: Final[int] = 7
    
    input_data_len: int = len(input_data)
    if input_data_len % 8:
        raise DecryptionError('input buffer size not a multiple of the block size')
    if input_data_len < 16:
        raise DecryptionError('input buffer size too small')
    
    cipher: TEACipher = TEACipher(key=key, rounds=32)
    
    dest_data: bytearray = cipher.decrypt(input_data)
    pad_len: int = dest_data[0] & 7
    out_len: int = input_data_len - 1 - pad_len - salt_len - zero_len
    if pad_len + salt_len != 8:
        raise DecryptionError(f'invalid pad len {pad_len + salt_len} (should be 8)')
    out_data: bytearray = bytearray(out_len)
    
    iv_prev: bytearray = bytearray(8)
    iv_cur: bytearray = input_data[:8]
    
    input_data_pos: int = 8
    
    dest_idx: int = pad_len + 1
    
    def crypt_block():
        nonlocal iv_prev, iv_cur, dest_data, input_data_pos, dest_idx
        
        iv_prev = iv_cur
        iv_cur = input_data[input_data_pos:input_data_pos + 8]
        
        dest_data = cipher.decrypt(xor_8bytes(dest_data, iv_cur))
        
        input_data_pos += 8
        dest_idx = 0
    
    i: int = 1
    while i <= salt_len:
        if dest_idx < 8:
            dest_idx += 1
            i += 1
        elif dest_idx == 8:
            crypt_block()
    
    out_pos: int = 0
    while out_pos < out_len:
        if dest_idx < 8:
            out_data[out_pos] = dest_data[dest_idx] ^ iv_prev[dest_idx]
            dest_idx += 1
            out_pos += 1
        elif dest_idx == 8:
            crypt_block()
    
    for i in range(1, zero_len):
        if dest_data[dest_idx] != iv_prev[dest_idx]:
            raise DecryptionError('zero check failed')
    
    return out_data


def decrypt_key(raw_key: BytesType) -> bytes:
    raw_key_decoded: bytes = b64decode(raw_key, validate=True)
    if len(raw_key_decoded) < 16:
        raise DecryptionError(f'key length is too short (must be greater than 16, got {len(raw_key_decoded)}')
    
    simple_key: bytearray = simple_make_key(salt=106, length=8)
    tea_key: bytearray = bytearray(16)
    for i in range(8):
        tea_key[i << 1] = simple_key[i]
        tea_key[(i << 1) + 1] = raw_key_decoded[i]
    
    rs: bytearray = decrypt_tc_tea(raw_key_decoded[8:], tea_key)
    
    return raw_key_decoded[:8] + rs
