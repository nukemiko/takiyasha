import json
import struct
from base64 import b64decode
from copy import deepcopy as dp
from typing import IO, Optional, Union

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad

from .ciphers import CacheCipher, RC4Cipher
from ..common import Decrypter

LE_Uint32: struct.Struct = struct.Struct('<I')


class NCMDecrypter(Decrypter):
    def __init__(self, **kwargs):
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
    def cover_data(self) -> Optional[str]:
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
            cipher: Union[RC4Cipher, CacheCipher] = RC4Cipher(master_key_data)
            
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
            cipher: Union[RC4Cipher, CacheCipher] = CacheCipher()
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
