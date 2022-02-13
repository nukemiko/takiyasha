import struct
from typing import IO, Optional, Type, Union

from .ciphers import (
    QMCv1_LegacyStaticMapCipher,
    QMCv1_StaticMapCipher,
    QMCv2_DynamicMapCipher,
    QMCv2_ModifiedRC4Cipher
)
from .keyutil import decrypt_key
from ..common import Cipher, Decoder
from ...exceptions import DecryptionError, ValidateFailed
from ...utils import get_audio_format, get_file_name_from_fileobj

QMC_Ciphers = Union[QMCv1_LegacyStaticMapCipher, QMCv1_StaticMapCipher, QMCv2_DynamicMapCipher, QMCv2_ModifiedRC4Cipher]
QMC_CiphersTypes = Type[QMC_Ciphers]

LE_Uint32 = struct.Struct('<L')
BE_Uint32 = struct.Struct('>L')

USE_LEGACY_QMCv1_CIPHER: bool = False


class QMCFormatDecoder(Decoder):
    @classmethod
    def _pre_create_instance(cls, file: IO[bytes]) -> tuple[bytes, Cipher, dict[str, ...]]:
        file.seek(0, 0)

        # 搜索和解密主密钥
        file_size_without_end_4bytes: int = file.seek(-4, 2)
        data: bytes = file.read(4)
        size: int = LE_Uint32.unpack(data)[0]

        if data == b'QTag':
            file.seek(-8, 2)
            data: bytes = file.read(4)
            raw_meta_len: int = BE_Uint32.unpack(data)[0] & 0xffffffffffffffff

            # 读取额外的元数据（songid等）
            audio_length: int = file.seek(-(8 + raw_meta_len), 2)
            raw_meta_data: bytes = file.read(raw_meta_len)

            items: list[bytes] = raw_meta_data.split(b',')
            if len(items) != 3:
                raise DecryptionError('invalid raw metadata')

            master_key: bytes = decrypt_key(items[0])

            raw_meta_extra1: Optional[int] = int(items[1])
            raw_meta_extra2: Optional[int] = int(items[2])
        else:
            raw_meta_extra1: Optional[int] = None
            raw_meta_extra2: Optional[int] = None
            if 0 < size < 0x300:
                audio_length: int = file.seek(-(4 + size), 2)
                raw_key_data: bytes = file.read(size)
                master_key: bytes = decrypt_key(raw_key_data)
            else:
                audio_length = file_size_without_end_4bytes + 4
                master_key: Optional[bytes] = None

        if master_key is None:
            if USE_LEGACY_QMCv1_CIPHER:
                cipher_cls: QMC_CiphersTypes = QMCv1_LegacyStaticMapCipher
            else:
                cipher_cls: QMC_CiphersTypes = QMCv1_StaticMapCipher
        else:
            key_length: int = len(master_key)
            if 0 < key_length <= 300:
                cipher_cls: QMC_CiphersTypes = QMCv2_DynamicMapCipher
            else:
                cipher_cls: QMC_CiphersTypes = QMCv2_ModifiedRC4Cipher
        cipher: QMC_Ciphers = cipher_cls(master_key)

        file.seek(0, 0)

        # 验证文件是否被QQ音乐加密
        decrypted_header_data: bytes = cipher.decrypt(file.read(32))
        audio_fmt: Optional[str] = get_audio_format(decrypted_header_data)
        if not audio_fmt:
            raise ValidateFailed(
                f"file '{get_file_name_from_fileobj(file)}' "
                f"is not encrypted by QQ Music"
            )

        file.seek(0, 0)

        raw_audio_data: bytes = file.read(audio_length)
        misc = {'audio_format': audio_fmt}
        if raw_meta_extra1 is not None:
            misc['song_id'] = raw_meta_extra1
        if raw_meta_extra2 is not None:
            misc['unknown_raw_meta_extra'] = raw_meta_extra2

        return raw_audio_data, cipher, misc

    @property
    def music_id(self) -> Optional[int]:
        return self._misc.get('song_id')
