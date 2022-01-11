import struct
from typing import IO, Optional, Union

from .ciphers import MapCipher, RC4Cipher, StaticMapCipher
from .key import decrypt_key
from ...exceptions import DecryptFailed, DecryptionError
from ...utils import get_file_ext_by_header

LE_Uint32 = struct.Struct('<L')
BE_Uint32 = struct.Struct('>L')


class QMCDecrypter:
    def __init__(self,
                 file: IO[bytes],
                 *,
                 audio_length: int,
                 cipher: Union[MapCipher, RC4Cipher, StaticMapCipher],
                 decrypted_key: bytes = None,
                 raw_metadata_extra: tuple[int, int] = None
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
        self._audio_length = audio_length
        self._decrypted_key = decrypted_key
        self._raw_metadata_extra = raw_metadata_extra
    
    @property
    def buffer(self):
        return self._buffer
    
    @property
    def cipher(self):
        return self._cipher
    
    @property
    def audio_length(self):
        return self._audio_length
    
    @property
    def decrypted_key(self):
        return self.decrypted_key
    
    @property
    def raw_metadata_extra(self):
        return self._raw_metadata_extra
    
    def decrypt(self) -> bytes:
        self.buffer.seek(0, 0)
        return self.cipher.decrypt(self.buffer.read(self.audio_length))
    
    @property
    def audio_format(self) -> str:
        """Return the format of decrypted audio data.
        
        :raise DecryptFailed: failed to recongize audio format.
        :return: audio format string"""
        self.buffer.seek(0, 0)
        test_data: bytes = self.buffer.read(32)
        
        decrypted_data: bytes = self.cipher.decrypt(test_data)
        fmt = get_file_ext_by_header(decrypted_data)
        
        if not fmt:
            raise DecryptFailed('failed to recongize decrypted audio format')
        else:
            return fmt
    
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
            
            decrypted_key: bytes = decrypt_key(items[0])
            
            raw_meta_extra1: int = int(items[1])
            raw_meta_extra2: int = int(items[2])
            raw_meta_extra: Optional[tuple[int, int]] = raw_meta_extra1, raw_meta_extra2
        else:
            raw_meta_extra = None
            if 0 < size < 0x300:
                audio_length: int = file.seek(-(4 + size), 2)
                raw_key_data: bytes = file.read(size)
                decrypted_key: bytes = decrypt_key(raw_key_data)
            else:
                audio_length = file_size_without_end_4bytes + 4
                decrypted_key: Optional[bytes] = None
        
        if decrypted_key is None:
            cipher = StaticMapCipher()
        else:
            key_length: int = len(decrypted_key)
            if 0 < key_length <= 300:
                cipher = MapCipher(decrypted_key)
            else:
                cipher = RC4Cipher(decrypted_key)
        
        file.seek(0, 0)
        
        return cls(
            file,
            audio_length=audio_length,
            decrypted_key=decrypted_key,
            cipher=cipher,
            raw_metadata_extra=raw_meta_extra
        )
