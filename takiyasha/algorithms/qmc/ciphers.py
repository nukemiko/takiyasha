import struct
from typing import Final, Optional

from ..common import Cipher
from ...exceptions import CipherGenerationError
from ...typehints import BytesType

BE_Uint32 = struct.Struct('>L')


class TEACipher(Cipher):
    """A cipher that implemented encryption and decryption of the Tiny Encryption Algorithm (TEA)."""
    
    def __init__(self,
                 key: BytesType,
                 rounds: int = 64,
                 magic_number: int = 0x9e3779b9
                 ):
        """Initialize self. See help(type(self)) for accurate signature."""
        if key is None:
            raise TypeError(f"'key' must be byte or bytearray, not None")
        super().__init__(key)
        
        self._block_size: Final[int] = 8
        self._delta: int = magic_number
        
        if self.key_length != 16:
            raise CipherGenerationError(f'incorrect key length {self.key_length} (should be 16)')
        if rounds & 1:
            raise CipherGenerationError(f'even number of rounds required (got {rounds})')
        
        self._rounds: int = rounds
    
    @property
    def block_size(self) -> int:
        return self._block_size
    
    @property
    def delta(self) -> int:
        return self._delta
    
    @property
    def rounds(self) -> int:
        return self._rounds
    
    def _put_uint32(self, value: int) -> bytearray:
        ret = bytearray(4)
        ret[0] = (value >> 24) % 256
        ret[1] = (value >> 16) % 256
        ret[2] = (value >> 8) % 256
        ret[3] = value % 256
        return ret
    
    def _get_values_from_src_data(self, src_data: BytesType, /) -> tuple[int, int, int, int, int, int]:
        v0: int = BE_Uint32.unpack(src_data[:4])[0]
        v1: int = BE_Uint32.unpack(src_data[4:8])[0]
        k0: int = BE_Uint32.unpack(self._key[:4])[0]
        k1: int = BE_Uint32.unpack(self._key[4:8])[0]
        k2: int = BE_Uint32.unpack(self._key[8:12])[0]
        k3: int = BE_Uint32.unpack(self._key[12:])[0]
        return v0, v1, k0, k1, k2, k3
    
    def decrypt(self, src_data: BytesType, /, offset: int = 0) -> bytearray:
        v0, v1, k0, k1, k2, k3 = self._get_values_from_src_data(src_data)
        
        delta: int = self.delta
        rounds: int = self.rounds
        
        ciphersum: int = (delta * (rounds // 2)) & 0xffffffff
        
        for i in range(rounds // 2):
            v1 -= ((v0 << 4) + k2) ^ (v0 + ciphersum) ^ ((v0 >> 5) + k3)
            v1 &= 0xffffffff
            v0 -= ((v1 << 4) + k0) ^ (v1 + ciphersum) ^ ((v1 >> 5) + k1)
            v0 &= 0xffffffff
            ciphersum -= delta
            ciphersum &= 0xffffffff
        
        ret = self._put_uint32(v0) + self._put_uint32(v1)
        return ret
    
    def encrypt(self, src_data: BytesType, /) -> bytearray:
        """Accept plain src_data and return the encrypted data."""
        v0, v1, k0, k1, k2, k3 = self._get_values_from_src_data(src_data)
        
        delta: int = self.delta
        rounds: int = self.rounds
        
        ciphersum: int = 0 & 0xffffffff
        
        for i in range(rounds // 2):
            ciphersum += delta
            ciphersum &= 0xffffffff
            v0 += ((v1 << 4) + k0) ^ (v1 + ciphersum) ^ ((v1 >> 5) + k1)
            v0 &= 0xffffffff
            v1 += ((v0 << 4) + k2) ^ (v0 + ciphersum) ^ ((v0 >> 5) + k3)
            v1 &= 0xffffffff
        
        ret = self._put_uint32(v0) + self._put_uint32(v1)
        return ret


class StaticMapCipher(Cipher):
    """A cipher that implemented decryption of the map-based QMCv1 encryption algorithm."""
    
    def __init__(self):
        """Initialize self. See help(type(self)) for accurate signature."""
        super().__init__(key=None)
        
        self.__static_cipher_box: Final[bytes] = bytes(
            [
                0x77, 0x48, 0x32, 0x73, 0xde, 0xf2, 0xc0, 0xc8,
                0x95, 0xec, 0x30, 0xb2, 0x51, 0xc3, 0xe1, 0xa0,
                0x9e, 0xe6, 0x9d, 0xcf, 0xfa, 0x7f, 0x14, 0xd1,
                0xce, 0xb8, 0xdc, 0xc3, 0x4a, 0x67, 0x93, 0xd6,
                0x28, 0xc2, 0x91, 0x70, 0xca, 0x8d, 0xa2, 0xa4,
                0xf0, 0x08, 0x61, 0x90, 0x7e, 0x6f, 0xa2, 0xe0,
                0xeb, 0xae, 0x3e, 0xb6, 0x67, 0xc7, 0x92, 0xf4,
                0x91, 0xb5, 0xf6, 0x6c, 0x5e, 0x84, 0x40, 0xf7,
                0xf3, 0x1b, 0x02, 0x7f, 0xd5, 0xab, 0x41, 0x89,
                0x28, 0xf4, 0x25, 0xcc, 0x52, 0x11, 0xad, 0x43,
                0x68, 0xa6, 0x41, 0x8b, 0x84, 0xb5, 0xff, 0x2c,
                0x92, 0x4a, 0x26, 0xd8, 0x47, 0x6a, 0x7c, 0x95,
                0x61, 0xcc, 0xe6, 0xcb, 0xbb, 0x3f, 0x47, 0x58,
                0x89, 0x75, 0xc3, 0x75, 0xa1, 0xd9, 0xaf, 0xcc,
                0x08, 0x73, 0x17, 0xdc, 0xaa, 0x9a, 0xa2, 0x16,
                0x41, 0xd8, 0xa2, 0x06, 0xc6, 0x8b, 0xfc, 0x66,
                0x34, 0x9f, 0xcf, 0x18, 0x23, 0xa0, 0x0a, 0x74,
                0xe7, 0x2b, 0x27, 0x70, 0x92, 0xe9, 0xaf, 0x37,
                0xe6, 0x8c, 0xa7, 0xbc, 0x62, 0x65, 0x9c, 0xc2,
                0x08, 0xc9, 0x88, 0xb3, 0xf3, 0x43, 0xac, 0x74,
                0x2c, 0x0f, 0xd4, 0xaf, 0xa1, 0xc3, 0x01, 0x64,
                0x95, 0x4e, 0x48, 0x9f, 0xf4, 0x35, 0x78, 0x95,
                0x7a, 0x39, 0xd6, 0x6a, 0xa0, 0x6d, 0x40, 0xe8,
                0x4f, 0xa8, 0xef, 0x11, 0x1d, 0xf3, 0x1b, 0x3f,
                0x3f, 0x07, 0xdd, 0x6f, 0x5b, 0x19, 0x30, 0x19,
                0xfb, 0xef, 0x0e, 0x37, 0xf0, 0x0e, 0xcd, 0x16,
                0x49, 0xfe, 0x53, 0x47, 0x13, 0x1a, 0xbd, 0xa4,
                0xf1, 0x40, 0x19, 0x60, 0x0e, 0xed, 0x68, 0x09,
                0x06, 0x5f, 0x4d, 0xcf, 0x3d, 0x1a, 0xfe, 0x20,
                0x77, 0xe4, 0xd9, 0xda, 0xf9, 0xa4, 0x2b, 0x76,
                0x1c, 0x71, 0xdb, 0x00, 0xbc, 0xfd, 0x0c, 0x6c,
                0xa5, 0x47, 0xf7, 0xf6, 0x00, 0x79, 0x4a, 0x11,
            ]
        )
    
    def _get_mask(self, offset: int) -> int:
        if offset > 0x7fff:
            offset %= 0x7fff
        idx: int = (offset ** 2 + 27) & 0xff
        return self.__static_cipher_box[idx]
    
    def decrypt(self, src_data: BytesType, /, offset: int = 0) -> bytes:
        """Accept encrypted src_data and return the decrypted data."""
        ret = bytes(src_data[i] ^ self._get_mask(offset=offset + i) for i in range(len(src_data)))
        return ret


class MapCipher(Cipher):
    """A cipher that implemented decryption of the map-based QMCv2 encryption algorithm.
    
    This cipher should be used if the key size is between [0, 300]."""
    
    def __init__(self, key: BytesType):
        """Initialize self. See help(type(self)) for accurate signature."""
        if key is None:
            raise TypeError(f"'key' must be byte or bytearray, not None")
        super().__init__(key)
    
    def _rotate(self, value: int, bits: int) -> int:
        rotated: int = (bits + 4) % 8
        left: int = (value << rotated) % 256
        right: int = (value >> rotated) % 256
        return left | right
    
    def _get_mask(self, offset: int) -> int:
        if offset > 0x7fff:
            offset %= 0x7fff
        idx: int = (offset ** 2 + 71214) % self.key_length
        return self._rotate(value=self.key[idx], bits=idx & 7)
    
    def decrypt(self, src_data: BytesType, /, offset: int = 0) -> bytes:
        """Accept encrypted src_data and return the decrypted data."""
        ret = bytes(src_data[i] ^ self._get_mask(offset=offset + i) for i in range(len(src_data)))
        return ret


class RC4Cipher(Cipher):
    """A cipher that implemented decryption of the RC4-based QMCv2 encryption algorithm.

    This cipher should be used if the key size is bigger than 300."""
    
    def __init__(self, key: BytesType):
        """Initialize self. See help(type(self)) for accurate signature."""
        if key is None:
            raise TypeError(f"'key' must be byte or bytearray, not None")
        super().__init__(key)
        
        self.__rc4_first_segment_size: Final[int] = 128
        self.__rc4_segment_size: Final[int] = 5120
        
        if self.key_length == 0:
            raise CipherGenerationError('invalid key size')
        
        # create and initialize S-box
        self._box: bytearray = bytearray(i % 256 for i in range(self.key_length))
        
        j: int = 0
        for i in range(self.key_length):
            j = (j + self._box[i] + key[i % self.key_length]) % self.key_length
            self._box[i], self._box[j] = self._box[j], self._box[i]
        
        self._hash: int = self._get_hash_base()
    
    @property
    def box(self) -> bytearray:
        return self._box
    
    @property
    def hash(self) -> int:
        return self._hash
    
    def _get_hash_base(self) -> int:
        hash_base = 1
        for i in range(self.key_length):
            v: int = self.key[i]
            if v == 0:
                continue
            next_hash: int = (hash_base * v) & 0xffffffff
            if next_hash == 0 or next_hash <= hash_base:
                break
            hash_base = next_hash
        return hash_base
    
    def _get_segment_skip(self, v: int) -> int:
        seed: int = self.key[v % self.key_length]
        idx: int = int(self.hash / ((v + 1) * seed) * 100)
        return idx % self.key_length
    
    def _enc_1st_segment(self, buf: BytesType, offset: int) -> bytearray:
        buf: bytearray = bytearray(buf)
        for i in range(len(buf)):
            buf[i] ^= self.key[self._get_segment_skip(offset + i)]
        return buf
    
    def _enc_another_segment(self, buf: BytesType, offset: int) -> bytearray:
        buf: bytearray = bytearray(buf)
        box: bytearray = self.box.copy()
        j, k = 0, 0
        
        skip_len: int = (offset % self.__rc4_segment_size) + self._get_segment_skip(offset // self.__rc4_segment_size)
        for i in range(-skip_len, len(buf)):
            j = (j + 1) % self.key_length
            k = (box[j] + k) % self.key_length
            box[j], box[k] = box[k], box[j]
            if i >= 0:
                buf[i] ^= box[(box[j] + box[k]) % self.key_length]
        return buf
    
    def decrypt(self, src_data: BytesType, /, offset: int = 0) -> Optional[bytes]:
        """Accept encrypted src_data and return the decrypted data."""
        src: bytearray = bytearray(src_data)
        pending: int = len(src_data)
        done: int = 0
        
        def mark_process(p: int) -> bool:
            nonlocal offset, pending, done
            offset += p
            pending -= p
            done += p
            return pending == 0
        
        if offset < self.__rc4_first_segment_size:
            blksize: int = pending
            if blksize > self.__rc4_first_segment_size - offset:
                blksize: int = self.__rc4_first_segment_size - offset
            target_slice: slice = slice(blksize)
            src[target_slice] = self._enc_1st_segment(src[target_slice], offset)
            pending_is_0: bool = mark_process(blksize)
            if pending_is_0:
                return bytes(src)
        
        if offset % self.__rc4_segment_size != 0:
            blksize: int = pending
            if blksize > self.__rc4_segment_size - (offset % self.__rc4_segment_size):
                blksize: int = self.__rc4_segment_size - (offset % self.__rc4_segment_size)
            target_slice: slice = slice(done, done + blksize)
            src[target_slice] = self._enc_another_segment(src[target_slice], offset)
            pending_is_0: bool = mark_process(blksize)
            if pending_is_0:
                return bytes(src)
        
        while pending > self.__rc4_segment_size:
            target_slice: slice = slice(done, done + self.__rc4_segment_size)
            src[target_slice] = self._enc_another_segment(src[target_slice], offset)
            mark_process(self.__rc4_segment_size)
        
        if pending > 0:
            src[done:] = self._enc_another_segment(src[done:], offset)
        
        return bytes(src)
