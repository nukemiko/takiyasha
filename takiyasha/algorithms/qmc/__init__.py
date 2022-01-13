import struct
from typing import IO, Optional

from .ciphers import MapCipher, RC4Cipher, StaticMapCipher
from .key import decrypt_key
from ..common import Decrypter
from ...exceptions import DecryptionError

LE_Uint32 = struct.Struct('<L')
BE_Uint32 = struct.Struct('>L')


class QMCDecrypter(Decrypter):
    def __init__(self, **kwargs):
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
            cipher = StaticMapCipher()
        else:
            key_length: int = len(master_key)
            if 0 < key_length <= 300:
                cipher = MapCipher(master_key)
            else:
                cipher = RC4Cipher(master_key)
        
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
