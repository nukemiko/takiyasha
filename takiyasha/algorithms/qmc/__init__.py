import struct
from typing import IO, Optional

from .ciphers import (
    QMCv1_ImprovedStaticMapCipher,
    QMCv1_StaticMapCipher,
    QMCv2_DynamicMapCipher,
    QMCv2_ImprovedDynamicMapCipher,
    QMCv2_ImprovedRC4Cipher,
    QMCv2_RC4Cipher
)
from .keyutil import decrypt_key
from ..common import CipherTypeVar, Decoder, Decrypter
from ...exceptions import DecryptionError

LE_Uint32 = struct.Struct('<L')
BE_Uint32 = struct.Struct('>L')


class QMCDecrypter(Decrypter):
    """The decrypter of QQMusic QMCv1 and QMCv2 encrypted file."""

    def __init__(self, **kwargs):
        """Initialize self. See help(type(self)) for accurate signature."""
        super().__init__(**kwargs)

        self._raw_metadata_extra: Optional[tuple[int, int]] = kwargs.pop('raw_metadata_extra')

    @property
    def raw_metadata_extra(self) -> Optional[tuple[int, int]]:
        return self._raw_metadata_extra

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

        # search and decrypt key
        file_size_without_end_4bytes: int = file.seek(-4, 2)
        data: bytes = file.read(4)
        size: int = LE_Uint32.unpack(data)[0]  # if data != b'QTag', this is the key size

        if data == b'QTag':
            file.seek(-8, 2)
            data: bytes = file.read(4)
            raw_meta_len: int = BE_Uint32.unpack(data)[0] & 0xffffffffffffffff

            # read raw meta data
            audio_length: int = file.seek(-(8 + raw_meta_len), 2)
            raw_meta_data: bytes = file.read(raw_meta_len)

            items: list[bytes] = raw_meta_data.split(b',')
            if len(items) != 3:
                raise DecryptionError('invalid raw metadata')

            master_key: bytes = decrypt_key(items[0])

            raw_meta_extra1: int = int(items[1])
            raw_meta_extra2: int = int(items[2])
            raw_meta_extra: Optional[tuple[int, int]] = raw_meta_extra1, raw_meta_extra2
        else:
            raw_meta_extra = None
            if 0 < size < 0x300:
                audio_length: int = file.seek(-(4 + size), 2)
                raw_key_data: bytes = file.read(size)
                master_key: bytes = decrypt_key(raw_key_data)
            else:
                audio_length = file_size_without_end_4bytes + 4
                master_key: Optional[bytes] = None

        if master_key is None:
            cipher = QMCv1_StaticMapCipher()
        else:
            key_length: int = len(master_key)
            if 0 < key_length <= 300:
                cipher = QMCv2_DynamicMapCipher(master_key)
            else:
                cipher = QMCv2_RC4Cipher(master_key)

        audio_start: int = 0

        file.seek(0, 0)

        return cls(
            buffer=file,
            cipher=cipher,
            master_key=master_key,
            audio_start=audio_start,
            audio_length=audio_length,
            raw_metadata_extra=raw_meta_extra
        )


class QMCDecoder(Decoder):
    @classmethod
    def _pre_create_instance(cls, file: IO[bytes]) -> tuple[bytes, CipherTypeVar, dict[str, ...]]:
        file.seek(0, 0)

        # search and decrypt key
        file_size_without_end_4bytes: int = file.seek(-4, 2)
        data: bytes = file.read(4)
        size: int = LE_Uint32.unpack(data)[0]

        if data == b'QTag':
            file.seek(-8, 2)
            data: bytes = file.read(4)
            raw_meta_len: int = BE_Uint32.unpack(data)[0] & 0xffffffffffffffff

            # read raw meta data
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
            cipher = QMCv1_ImprovedStaticMapCipher()
        else:
            key_length: int = len(master_key)
            if 0 < key_length <= 300:
                cipher = QMCv2_ImprovedDynamicMapCipher(master_key)
            else:
                cipher = QMCv2_ImprovedRC4Cipher(master_key)

        file.seek(0, 0)
        raw_audio_data: bytes = file.read(audio_length)
        misc = {}
        if raw_meta_extra1 is not None:
            misc['song_id'] = raw_meta_extra1
        if raw_meta_extra2 is not None:
            misc['unknown_raw_meta_extra'] = raw_meta_extra2

        return raw_audio_data, cipher, misc

    @property
    def music_id(self) -> Optional[int]:
        return self._misc.get('song_id')
