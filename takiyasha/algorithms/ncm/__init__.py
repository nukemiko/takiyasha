import json
import struct
from base64 import b64decode
from copy import deepcopy as dp
from typing import IO, Optional, Union

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad

from .ciphers import (
    NCM_ImprovedRC4Cipher,
    NCM_ImprovedXORCipher,
    NCM_RC4Cipher,
    NCM_XOROnlyCipher
)
from ..common import (
    CipherTypeVar,
    Decoder,
    Decrypter
)
from ...exceptions import DecryptionError
from ...utils import (
    get_file_ext_by_header, get_file_name_from_fileobj
)

LE_Uint32: struct.Struct = struct.Struct('<I')


class NCMDecrypter(Decrypter):
    """The decrypter of Cloudmusic NCM encrypted container format."""

    def __init__(self, **kwargs):
        """Initialize self. See help(type(self)) for accurate signature."""
        super().__init__(**kwargs)

        self._metadata: dict[str, Union[str, list]] = kwargs.pop('metadata')
        self._identifier: str = kwargs.pop('identifier')
        self._cover_data: Optional[bytes] = kwargs.pop('cover_data')

    @property
    def metadata(self) -> dict[str, Union[str, list]]:
        return dp(self._metadata)

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def cover_data(self) -> Optional[bytes]:
        return self._cover_data

    @classmethod
    def new(cls, file: IO[bytes]):
        # check whether file is readable and seekable
        try:
            if not (file.readable() and file.read):
                raise OSError('file is not readable')
            if not (file.seekable() and file.seek):
                raise OSError('file is not seekable')
        except AttributeError:
            raise TypeError(f"'file' must be readable and seekable file object, not {type(file).__name__}")

        file.seek(0, 0)  # ensure offset is 0

        # judge file type by magic header
        if file.read(8) == b'CTENFDAM':
            # is NCM encrypted file
            file.seek(2, 1)

            # read and decrypt master key
            raw_master_key_len: int = LE_Uint32.unpack(file.read(4))[0]
            raw_master_key_data: bytes = bytes(b ^ 100 for b in file.read(raw_master_key_len))
            aes_crypter = AES.new(b'hzHRAmso5kInbaxW', AES.MODE_ECB)
            master_key_data: bytes = unpad(aes_crypter.decrypt(raw_master_key_data), 16)[17:]
            master_key: Optional[bytes] = master_key_data

            # generate RC4Cipher use master key
            cipher: Union[NCM_RC4Cipher, NCM_XOROnlyCipher] = NCM_RC4Cipher(master_key_data)

            # read and decrypt metadata
            raw_metadada_len: int = LE_Uint32.unpack(file.read(4))[0]
            if raw_metadada_len:
                raw_metadata: bytes = bytes(b ^ 99 for b in file.read(raw_metadada_len))
                identifier: str = raw_metadata.decode()
                encrypted_metadata: bytes = b64decode(raw_metadata[22:])

                aes_crypter = AES.new(b"#14ljk_!\\]&0U<'(", AES.MODE_ECB)
                metadata: dict = json.loads(unpad(aes_crypter.decrypt(encrypted_metadata), 16)[6:])
            else:
                identifier: str = ''
                metadata: dict = {}

            file.seek(5, 1)

            # read cover data
            cover_space: int = LE_Uint32.unpack(file.read(4))[0]
            cover_size: int = LE_Uint32.unpack(file.read(4))[0]
            cover_data: Optional[bytes] = file.read(cover_size) if cover_size else None
            file.seek(cover_space - cover_size, 1)

            audio_start: int = file.tell()
        else:
            # is encrypted Cloudmusic cache file
            cipher: Union[NCM_RC4Cipher, NCM_XOROnlyCipher] = NCM_XOROnlyCipher()
            audio_start: int = 0
            metadata: dict = {}
            identifier: str = ''
            cover_data: Optional[bytes] = None
            master_key: Optional[bytes] = None

        audio_length: int = file.seek(0, 2) - audio_start

        return cls(
            buffer=file,
            cipher=cipher,
            master_key=master_key,
            audio_start=audio_start,
            audio_length=audio_length,
            metadata=metadata.copy(),
            identifier=identifier,
            cover_data=cover_data
        )


class NCMFormatDecoder(Decoder):
    @classmethod
    def _pre_create_instance(cls, file: IO[bytes]) -> tuple[bytes, CipherTypeVar, dict[str, ...]]:
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

            # 使用 master_key 创建 RC4Cipher
            cipher: CipherTypeVar = NCM_ImprovedRC4Cipher(master_key)

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
        else:
            # 文件或许是网易云音乐的加密缓存
            file.seek(0, 0)

            cipher: CipherTypeVar = NCM_ImprovedXORCipher()
            metadata: dict[str, Union[str, list[Union[str, list[str]]], bytes]] = {}

            # 验证文件是否被网易云音乐加密
            header_data: bytes = file.read(32)
            if not get_file_ext_by_header(header_data):
                raise DecryptionError(
                    f"file '{get_file_name_from_fileobj(file)}' "
                    f"is not encrypted by Cloudmusic"
                )

            raw_audio_data: bytes = header_data + file.read()

        return raw_audio_data, cipher, {'metadata': metadata}

    def __init__(
            self,
            raw_audio_data: bytes,
            cipher: CipherTypeVar,
            misc: dict[str, ...],
            filename: str
    ):
        super().__init__(raw_audio_data, cipher, misc, filename)

    @property
    def _metadata(self) -> dict[str, Union[str, list[Union[str, list[str]]], bytes]]:
        return self._misc['metadata']

    @property
    def music_title(self) -> Optional[str]:
        return self._metadata.get('musicName')

    @property
    def music_id(self) -> Optional[int]:
        if self._metadata.get('musicId'):
            return int(self._metadata.get('musicId'))

    @property
    def music_artists(self) -> Optional[list[str]]:
        if self._metadata.get('artist'):
            return [item[0] for item in self._metadata.get('artist')]

    @property
    def music_album(self) -> Optional[str]:
        return self._metadata.get('album')

    @property
    def music_album_id(self) -> Optional[int]:
        if self._metadata.get('albumId'):
            return int(self._metadata.get('albumId'))

    @property
    def music_platform_alias(self) -> Optional[list[str]]:
        return self._metadata.get('alias')

    @property
    def music_identifiers(self) -> Optional[str]:
        return self._metadata.get('identifier')
