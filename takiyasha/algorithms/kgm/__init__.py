from struct import Struct
from typing import IO, Optional
from warnings import warn

from .ciphers import KGM_MaskCipher
from ..common import Cipher, Decoder
from ...exceptions import DecryptionError, DecryptionWarning, ValidateFailed
from ...utils import get_audio_format, get_file_name_from_fileobj

LE_Uint32: Struct = Struct('<I')
_VPR_HEADER: bytes = bytes(
    [
        0x05, 0x28, 0xbc, 0x96, 0xe9, 0xe4, 0x5a, 0x43,
        0x91, 0xaa, 0xbd, 0xd0, 0x7a, 0xf5, 0x36, 0x31
    ]
)
_KGM_HEADER: bytes = bytes(
    [
        0x7c, 0xd5, 0x32, 0xeb, 0x86, 0x02, 0x7f, 0x4b,
        0xa8, 0xaf, 0xa6, 0x8e, 0x0f, 0xff, 0x99, 0x14
    ]
)


class KGMFormatDecoder(Decoder):
    @classmethod
    def _pre_create_instance(cls, file: IO[bytes]) -> tuple[bytes, Cipher, dict[str, ...]]:
        file.seek(0x10, 0)
        header_len: int = LE_Uint32.unpack(file.read(4))[0]
        file.seek(0, 0)
        header_data: bytes = file.read(header_len)
        if header_data.startswith(_KGM_HEADER):
            is_vpr: bool = False
        elif header_data.startswith(_VPR_HEADER):
            is_vpr: bool = True
        else:
            raise DecryptionError('kgm/vpr magic header not matched')

        file.seek(0x1c, 0)
        master_key1: bytes = file.read(16) + b'\x00'
        # master_key2: bytes = file.read(16)  # 未解决：key2

        cipher: KGM_MaskCipher = KGM_MaskCipher(master_key1, is_vpr_format=is_vpr)
        file.seek(header_len, 0)
        raw_audio_data: bytes = file.read()

        if cipher.full_mask_length < len(raw_audio_data):
            print(1)
            warn(
                DecryptionWarning(
                    'The file is too large and the processed audio is incomplete '
                    f'({len(raw_audio_data)} > {cipher.full_mask_length})'
                )
            )
            raw_audio_data: bytes = raw_audio_data[:cipher.full_mask_length]

        # 验证文件是否被加密
        decrypted_header_data: bytes = cipher.decrypt(raw_audio_data[:32])
        audio_fmt: Optional[str] = get_audio_format(decrypted_header_data)
        if not audio_fmt:
            raise ValidateFailed(
                f"file '{get_file_name_from_fileobj(file)}' "
                f"is not encrypted by Kugou"
            )

        return raw_audio_data, cipher, {'audio_format': audio_fmt}
