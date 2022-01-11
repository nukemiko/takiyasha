import json
import struct
from base64 import b64decode
from typing import IO, Optional, Union

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad

from .ciphers import CacheCipher, RC4Cipher

LE_Uint32: struct.Struct = struct.Struct('<I')


class NCMDecrypter:
    def __init__(self,
                 file: IO[bytes],
                 *,
                 cipher: Union[RC4Cipher, CacheCipher],
                 audio_start: int,
                 key: bytes = None,
                 metadata: dict = None,
                 metadata_identifier: str = None,
                 cover_data: bytes = None
                 ):
        # check whether the object is a file object
        readfunc = file.read
        seekfunc = file.seek
        if not readfunc:
            raise TypeError(f"'file' must be file object, not {type(file)}")
        elif not seekfunc:
            raise ValueError('file object is not seekable')
        
        file.seek(0, 0)  # ensure offset is 0
        
        self._buffer = file
        self._cipher = cipher
        self._audio_start = audio_start
        self._key = key
        self._metadata = metadata
        self._metadata_identifier = metadata_identifier
        self._cover_data = cover_data
    
    @property
    def buffer(self):
        return self._buffer
    
    @property
    def cipher(self):
        return self._cipher
    
    @property
    def audio_start(self):
        return self._audio_start
    
    @property
    def key(self):
        return self._key
    
    @property
    def metadata(self):
        return self._metadata
    
    @property
    def metadata_identifier(self):
        return self._metadata_identifier
    
    @property
    def cover_data(self):
        return self._cover_data
    
    def decrypt(self):
        self.buffer.seek(self.audio_start)
        return self.cipher.decrypt(self.buffer.read())
    
    @classmethod
    def generate(cls, file: IO[bytes]):
        # check whether the object is a file object
        readfunc = file.read
        seekfunc = file.seek
        if not readfunc:
            raise TypeError(f"'file' must be file object, not {type(file)}")
        elif not seekfunc:
            raise ValueError('file object is not seekable')
        
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
            key: Optional[bytes] = master_key_data
            
            # generate RC4Cipher use master key
            cipher: Union[RC4Cipher, CacheCipher] = RC4Cipher(master_key_data)
            
            # read and decrypt metadata
            raw_metadada_len: int = LE_Uint32.unpack(file.read(4))[0]
            if raw_metadada_len:
                raw_metadata: bytes = bytes(b ^ 99 for b in file.read(raw_metadada_len))
                metadata_identifier: str = raw_metadata.decode()
                encrypted_metadata: bytes = b64decode(raw_metadata[22:])
                
                aes_crypter = AES.new(b"#14ljk_!\\]&0U<'(", AES.MODE_ECB)
                metadata: dict = json.loads(unpad(aes_crypter.decrypt(encrypted_metadata), 16)[6:])
            else:
                metadata_identifier: str = ''
                metadata: dict = {}
            
            file.seek(5, 1)
            
            # read cover data
            cover_space: int = LE_Uint32.unpack(file.read(4))[0]
            cover_size: int = LE_Uint32.unpack(file.read(4))[0]
            cover_data: Optional[bytes] = file.read(cover_size) if cover_size else None
            file.seek(cover_space - cover_size, 1)
            
            audio_start: int = file.seek(0, 1)
        else:
            # is encrypted Cloudmusic cache file
            cipher: Union[RC4Cipher, CacheCipher] = CacheCipher()
            audio_start: int = 0
            metadata: dict = {}
            metadata_identifier: str = ''
            cover_data: Optional[bytes] = None
            key: Optional[bytes] = None
        
        return cls(
            file,
            cipher=cipher,
            audio_start=audio_start,
            key=key,
            metadata=metadata.copy(),
            metadata_identifier=metadata_identifier,
            cover_data=cover_data
        )
