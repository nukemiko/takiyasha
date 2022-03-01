import json
from base64 import b64decode
from struct import Struct
from typing import IO, Optional, Type, Union

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad

from .ciphers import (
    NCM_RC4Cipher,
    NCM_XorOnlyCipher,
)
from ..common import Decoder
from ...exceptions import ValidateFailed
from ...utils import (
    get_audio_format,
    get_file_name_from_fileobj
)

NCM_Ciphers = Union[NCM_RC4Cipher, NCM_XorOnlyCipher]
NCM_CiphersTypes = Type[NCM_Ciphers]

LE_Uint32: Struct = Struct('<I')


class NCMFormatDecoder(Decoder):
    @classmethod
    def _pre_create_instance(cls, file: IO[bytes]) -> tuple[bytes, NCM_Ciphers, dict[str, ...]]:
        file.seek(0, 0)

        # 根据文件前8个字节判断文件类型
        if file.read(8) == b'CTENFDAM':
            # 文件是 NCM 加密容器格式
            file.seek(2, 1)

            # 读取和解密主密钥
            raw_master_key_len: int = LE_Uint32.unpack(file.read(4))[0]
            raw_master_key_data: bytes = bytes(b ^ 100 for b in file.read(raw_master_key_len))
            aes_crypter = AES.new(b'hzHRAmso5kInbaxW', AES.MODE_ECB)
            master_key: bytes = unpad(aes_crypter.decrypt(raw_master_key_data), 16)[17:]

            # 读取和解密元数据
            raw_metadada_len: int = LE_Uint32.unpack(file.read(4))[0]
            if raw_metadada_len:
                raw_metadata: bytes = bytes(b ^ 99 for b in file.read(raw_metadada_len))
                identifier: str = raw_metadata.decode()
                encrypted_metadata: bytes = b64decode(raw_metadata[22:])

                aes_crypter = AES.new(b"#14ljk_!\\]&0U<'(", AES.MODE_ECB)
                metadata: dict[str, Union[str, list[Union[str, list[str]]], bytes]] = json.loads(unpad(aes_crypter.decrypt(encrypted_metadata), 16)[6:])
            else:
                identifier: str = ''
                metadata: dict[str, Union[str, list[Union[str, list[str]]], bytes]] = {}

            file.seek(5, 1)

            # 读取封面数据
            cover_space: int = LE_Uint32.unpack(file.read(4))[0]
            cover_size: int = LE_Uint32.unpack(file.read(4))[0]
            cover_data: Optional[bytes] = file.read(cover_size) if cover_size else None
            file.seek(cover_space - cover_size, 1)

            # 将封面数据和网易云音乐独有标识加入元数据
            metadata['cover_data'] = cover_data
            metadata['identifier'] = identifier

            # 读取剩余的加密音频数据
            raw_audio_data: bytes = file.read()
            cipher_cls: NCM_CiphersTypes = NCM_RC4Cipher
        else:
            # 文件或许是网易云音乐的加密缓存
            file.seek(0, 0)

            cipher_cls: NCM_CiphersTypes = NCM_XorOnlyCipher
            master_key: Optional[bytes] = None
            raw_audio_data: bytes = file.read()
            metadata: dict[str, Union[str, list[Union[str, list[str]]], bytes]] = {}

        cipher: NCM_Ciphers = cipher_cls(master_key)

        # 验证文件是否被网易云音乐加密，同时猜测音频格式
        decrypted_header_data: bytes = cipher.decrypt(raw_audio_data[:32])
        audio_fmt: Optional[str] = get_audio_format(decrypted_header_data)
        if not audio_fmt:
            raise ValidateFailed(
                f"file '{get_file_name_from_fileobj(file)}' "
                f"is not encrypted by Cloudmusic"
            )

        return raw_audio_data, cipher, {'metadata': metadata, 'audio_format': audio_fmt}

    @property
    def metadata(self) -> dict[str, Union[str, list[Union[str, list[str]]], bytes]]:
        return self._misc['metadata']

    @property
    def music_title(self) -> Optional[str]:
        return self.metadata.get('musicName')

    @property
    def music_id(self) -> Optional[int]:
        if self.metadata.get('musicId'):
            return int(self.metadata.get('musicId'))

    @property
    def music_artists(self) -> Optional[list[str]]:
        if self.metadata.get('artist'):
            return [item[0] for item in self.metadata.get('artist')]

    @property
    def music_album(self) -> Optional[str]:
        return self.metadata.get('album')

    @property
    def music_album_id(self) -> Optional[int]:
        if self.metadata.get('albumId'):
            return int(self.metadata.get('albumId'))

    @property
    def music_platform_alias(self) -> Optional[list[str]]:
        return self.metadata.get('alias')

    @property
    def music_identifier(self) -> Optional[str]:
        return self.metadata.get('identifier')

    @property
    def music_cover_data(self) -> Optional[bytes]:
        return self.metadata.get('cover_data')
