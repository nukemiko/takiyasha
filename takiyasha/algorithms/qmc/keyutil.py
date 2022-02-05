from base64 import b64decode
from math import tan

from .ciphers import TC_ModifiedTEACipher
from ...exceptions import DecryptionError


def generate_simple_key(salt: int, length: int) -> bytes:
    return bytes(
        int(abs(tan(salt + i * 0.1)) * 100) for i in range(length)
    )


def decrypt_key(raw_key: bytes) -> bytes:
    raw_key_decoded: bytes = b64decode(raw_key, validate=True)
    if len(raw_key_decoded) < 16:
        raise DecryptionError(f'key length is too short (must be greater than 16, got {len(raw_key_decoded)}')

    simple_key: bytes = generate_simple_key(106, 8)
    tea_key: bytearray = bytearray(16)
    for i in range(8):
        tea_key[i << 1] = simple_key[i]
        tea_key[(i << 1) + 1] = raw_key_decoded[i]

    rs: bytes = TC_ModifiedTEACipher(bytes(tea_key), rounds=32).decrypt(raw_key_decoded[8:])

    return raw_key_decoded[:8] + rs
