from typing import IO

from .ciphers import TM_Cipher
from ..common import Cipher, Decoder
from ...exceptions import DecryptionError, ValidateFailed
from ...utils import get_file_name_from_fileobj


class TMFormatDecoder(Decoder):
    @classmethod
    def _pre_create_instance(cls, file: IO[bytes]) -> tuple[bytes, Cipher, dict[str, ...]]:
        header: bytes = file.read(4)
        # 通过文件前4个字节判断是否为 TM 格式文件
        if header != b'\x51\x51\x4d\x55':
            raise ValidateFailed(
                f"file '{get_file_name_from_fileobj(file)}' "
                f"is not encrypted by QQ Music"
            )

        file.seek(0, 0)
        raw_audio_data: bytes = file.read()

        # 如果文件长度小于8，则文件无效
        if len(raw_audio_data) < 8:
            raise DecryptionError(
                f'invalid data size {len(raw_audio_data)} '
                f'(should be greater or equal to 8)'
            )

        return raw_audio_data, TM_Cipher(), {}
