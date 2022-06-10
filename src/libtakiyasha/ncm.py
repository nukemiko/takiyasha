from __future__ import annotations

import json
from base64 import b64decode, b64encode
from copy import deepcopy as dp
from io import BytesIO
from random import randrange
from string import digits as strdigits
from typing import Generator, IO

from . import utils
from .common import Cipher, Crypter
from .exceptions import FileTypeMismatchError
from .standardciphers import StreamedAESWithModeECB

__all__ = ['NCM', 'NCMRC4Cipher']


class NCMRC4Cipher(Cipher):
    @staticmethod
    def cipher_name() -> str:
        return 'RC4'

    def __init__(self, key: bytes) -> None:
        super().__init__(key)

        # 使用 RC4-KSA 生成 S-box
        S = bytearray(range(256))
        j = 0
        key_len = len(key)
        for i in range(256):
            j = (j + S[i] + key[i % key_len]) & 0xff
            S[i], S[j] = S[j], S[i]

        # 使用 PRGA 从 S-box 生成密钥流
        stream_short = bytearray(256)
        for i in range(256):
            _ = (i + 1) & 0xff
            si = S[_] & 0xff
            sj = S[(_ + si) & 0xff] & 0xff
            stream_short[i] = S[(si + sj) & 0xff]

        self._keystream_short = stream_short

    def yield_keystream(self, src_len: int, offset: int) -> Generator[int, None, None]:
        keystream_short = self._keystream_short

        for i in range(offset, offset + src_len):
            yield keystream_short[i & 0xff]

    def decrypt(self, cipherdata: bytes, start_offset: int = 0) -> bytes:
        cipherdata_len = len(cipherdata)
        return utils.bytesxor(cipherdata, bytes(self.yield_keystream(cipherdata_len, start_offset)))


class NCM(Crypter):
    """读写网易云音乐 NCM 格式的文件。

    读取：

    >>> ncmfile = NCM('./test1.ncm')
    >>> data = ncmfile.read()

    写入：

    >>> ncmfile.write(b'Writted bytes')

    创建、写入并保存：

    >>> new_ncmfile = NCM()  # 随机生成一个密钥
    >>> with open('./metal.flac', 'rb') as f:  # 写入未加密的文件数据
    ...     new_ncmfile.write(f.read())
    >>> new_ncmfile.save('./result.ncm')
    >>> """

    @staticmethod
    def core_key() -> bytes:
        return b'\x68\x7a\x48\x52\x41\x6d\x73\x6f\x35\x6b\x49\x6e\x62\x61\x78\x57'

    @staticmethod
    def meta_key():
        return b'\x23\x31\x34\x6c\x6a\x6b\x5f\x21\x5c\x5d\x26\x30\x55\x3c\x27\x28'

    @staticmethod
    def file_headers() -> dict[bytes, str]:
        return {
            b'CTENFDAM': 'NCM'
        }

    def __init__(self,
                 filething: utils.FileThing | None = None,
                 **kwargs
                 ) -> None:
        """读写网易云音乐 NCM 格式的文件。

        Args:
            filething (file): 源 NCM 文件的路径或文件对象；留空则视为创建一个空 NCM 文件
        Keyword Args:
            key (bytes): 加/解密数据所需的密钥；留空则会随机生成一个

        所有未知的关键字参数都会被忽略。
        """
        if filething is None:
            self._raw = BytesIO()
            self._name = None

            key: bytes | None = kwargs.get('key', None)
            if key is not None:
                self._cipher: NCMRC4Cipher = NCMRC4Cipher(key)
            else:
                # 如果没有指定密钥，也没有指定文件，那么随机生成一个长度等于 111 或 113 的密钥
                key_left = utils.gen_random_string(
                    randrange(27, 30), strdigits
                ).encode()
                key_right = b'E7fT49x7dof9OKCgg9cdvhEuezy3iZCL1nFvBFd1T4uSktAJKmwZXsijPbijliionVUXXg9plTbXEclAE9Lb'
                self._cipher = NCMRC4Cipher(key_left + key_right)

            self._tagdata = {}
            self.coverdata = b''
        else:
            super().__init__(filething, **kwargs)

    def load(self,
             filething: utils.FileThing,
             **kwargs
             ) -> None:
        """将一个 NCM 文件加载到当前 NCM 对象中。

        Args:
            filething (file): 源 NCM 文件的路径或文件对象
        Keyword Args:
            skip_tagdata (bool): 加载文件时跳过加载标签信息和封面数据，默认为 ``False``
        Raises:
            FileTypeMismatchError: ``filething`` 不是一个 NCM 格式文件

        所有未知的关键字参数都会被忽略。
        """
        skip_tagdata: bool = kwargs.get('skip_tagdata', False)

        if utils.is_filepath(filething):
            fileobj: IO[bytes] = open(filething, 'rb')  # type: ignore
            self._name = fileobj.name
        else:
            fileobj: IO[bytes] = filething  # type: ignore
            self._name = None
            utils.verify_fileobj_readable(fileobj, bytes)
            utils.verify_fileobj_seekable(fileobj)

        fileobj.seek(0, 0)

        file_header = fileobj.read(10)
        for header in self.file_headers():
            if file_header.startswith(header):
                break
        else:
            raise FileTypeMismatchError('not a NCM file: bad file header')

        # 获取加密的主密钥数据
        encrypted_masterkey_len = int.from_bytes(fileobj.read(4), 'little')
        encrypted_masterkey = bytes(b ^ 0x64 for b in fileobj.read(encrypted_masterkey_len))
        masterkey_cipher = StreamedAESWithModeECB(self.core_key())
        masterkey = masterkey_cipher.decrypt(encrypted_masterkey)[17:]  # 去除密钥开头的 b'neteasecloudmusic'

        # 获取加密的标签信息
        raw_encrypted_tagdata_len = int.from_bytes(fileobj.read(4), 'little')
        tagdata = {}
        if skip_tagdata:
            fileobj.seek(raw_encrypted_tagdata_len, 1)
        else:
            raw_encrypted_tagdata = bytes(
                b ^ 0x63 for b in fileobj.read(raw_encrypted_tagdata_len)
            )
            encrypted_tagdata = b64decode(raw_encrypted_tagdata[22:], validate=True)  # 在 b64decode 之前，去除原始数据开头的 b"163 key(Don't modify):"
            identifier = raw_encrypted_tagdata
            tagdata_cipher = StreamedAESWithModeECB(self.meta_key())
            tagdata.update(json.loads(tagdata_cipher.decrypt(encrypted_tagdata)[6:]))  # 在 JSON 反序列化之前，去除字节串开头的 b'music:'
            tagdata['identifier'] = identifier.decode()

        fileobj.seek(5, 1)

        # 获取封面数据
        cover_alloc = int.from_bytes(fileobj.read(4), 'little')
        coverdata = b''
        if skip_tagdata:
            fileobj.seek(cover_alloc, 1)
        else:
            cover_size = int.from_bytes(fileobj.read(4), 'little')
            if cover_size:
                coverdata = fileobj.read(cover_size)
            fileobj.seek(cover_alloc - cover_size, 1)

        # 将以上步骤所得信息，连同加密音频数据设置为属性
        self._tagdata = tagdata
        self.coverdata = coverdata
        self._cipher: NCMRC4Cipher = NCMRC4Cipher(masterkey)
        self._raw = BytesIO(fileobj.read())

    def save(self,
             filething: utils.FileThing | None = None,
             **kwargs
             ) -> None:
        """将当前 NCM 对象保存为一个 NCM 格式文件。

        Args:
            filething (file): 目标 NCM 文件的路径或文件对象，
                留空则尝试使用 ``self.name``；如果两者都为空，
                抛出 ``ValueError``
        Keyword Args:
            tagdata (dict): 向目标文件写入的标签信息；留空则使用 ``self.tagdata``
            coverdata (bytes): 向目标文件写入的封面数据；留空则使用 ``self.coverdata``
        Raises:
            ValueError: 同时缺少参数 ``filething`` 和属性 ``self.name``

        所有未知的关键字参数都会被忽略。
        """
        tagdata: dict | None = kwargs.get('tagdata', None)
        coverdata: bytes | None = kwargs.get('coverdata', None)

        if filething:
            if utils.is_filepath(filething):
                fileobj: IO[bytes] = open(filething, 'wb')  # type: ignore
            else:
                fileobj: IO[bytes] = filething  # type: ignore
                utils.verify_fileobj_writable(fileobj, bytes)
        elif self._name:
            fileobj: IO[bytes] = open(self._name, 'wb')
        else:
            raise ValueError('missing filepath or fileobj')
        if tagdata is None:
            tagdata = dp(self._tagdata)
        else:
            tagdata = dp(tagdata)
        if coverdata is None:
            coverdata = bytes(self.coverdata)

        fileobj.seek(0, 0)

        fileobj.write(b'CTENFDAM\x00\x00')

        # 加密并写入主密钥
        masterkey = b'neteasecloudmusic' + self._cipher.key
        masterkey_cipher = StreamedAESWithModeECB(self.core_key())
        encrypted_masterkey = bytes(b ^ 0x64 for b in masterkey_cipher.encrypt(masterkey))
        fileobj.write(len(encrypted_masterkey).to_bytes(4, 'little'))
        fileobj.write(encrypted_masterkey)

        # 加密并写入标签信息
        tagdata.pop('identifier', None)
        plain_tagdata = b'music:' + json.dumps(tagdata).encode()
        tagdata_cipher = StreamedAESWithModeECB(self.meta_key())
        encrypted_tagdata = tagdata_cipher.encrypt(plain_tagdata)
        raw_encrypted_tagdata = bytes(b ^ 0x63 for b in b"163 key(Don't modify):" + b64encode(encrypted_tagdata))
        fileobj.write(len(raw_encrypted_tagdata).to_bytes(4, 'little'))
        fileobj.write(raw_encrypted_tagdata)

        fileobj.seek(5, 1)

        # 写入封面数据
        cover_alloc = len(coverdata)
        cover_size = cover_alloc
        fileobj.write(cover_alloc.to_bytes(4, 'little'))
        fileobj.write(cover_size.to_bytes(4, 'little'))
        fileobj.write(coverdata)

        # 写入加密的音频数据
        self._raw.seek(0, 0)
        fileobj.write(self._raw.read())

        if utils.is_filepath(filething):
            fileobj.close()

    @property
    def tagdata(self) -> dict:
        return self._tagdata
