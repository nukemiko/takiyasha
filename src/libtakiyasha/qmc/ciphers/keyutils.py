from __future__ import annotations

from base64 import b64decode, b64encode
from typing import IO

from . import legacyconstants
from .legacy import Key256Mask128
from ... import utils
from ...standardciphers import TencentTEAWithModeCBC

__all__ = ['QMCv2_key_decrypt', 'QMCv2_key_encrypt', 'find_mflac_mask', 'find_mgg_mask']


def QMCv2_key_decrypt(ciphered_keydata: bytes) -> bytes:
    decoded_ciphered_keydata = b64decode(ciphered_keydata, validate=True)
    tea_key_recipe = decoded_ciphered_keydata[:8]
    ciphered_segment = decoded_ciphered_keydata[8:]

    cipher = TencentTEAWithModeCBC.from_recipe(tea_key_recipe, rounds=32)

    return tea_key_recipe + cipher.decrypt(ciphered_segment, zero_check=True)


def QMCv2_key_encrypt(plain_keydata: bytes) -> bytes:
    tea_key_recipe = plain_keydata[:8]
    plain_segment = plain_keydata[8:]

    cipher = TencentTEAWithModeCBC.from_recipe(tea_key_recipe, rounds=32)

    ciphered_keydata = tea_key_recipe + cipher.encrypt(plain_segment)

    return b64encode(ciphered_keydata)


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
