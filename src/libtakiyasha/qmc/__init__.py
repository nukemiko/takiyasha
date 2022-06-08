from __future__ import annotations

from io import BytesIO
from typing import IO, Literal

from .ciphers import keyutils
from .ciphers.legacy import Key256Mask128, OldStaticMap
from .ciphers.modern import DynamicMap, ModifiedRC4, StaticMap
from .. import utils
from ..common import Crypter
from ..exceptions import FileTypeMismatchError, InvalidDataError, UnsupportedFileType

__all__ = ['QMCv1', 'QMCv2']


class QMCv1(Crypter):
    """读写 QQ 音乐 QMCv1 格式的文件。

    读取：

    >>> qmcv1file = QMCv1('./test.qmcflac')
    >>> data = qmcv1file.read()
    >>>

    写入：

    >>> qmcv1file.write(b'Writted bytes')
    >>>

    创建、写入并保存：

    >>> new_qmcv1file = QMCv1()
    >>> with open('./source.flac', 'rb') as f:  # 写入未加密的文件数据
    ...     new_qmcv1file.write(f.read())
    >>> new_qmcv1file.save('./result.qmcflac')
    >>>
    """

    @staticmethod
    def file_headers() -> dict[bytes, str]:
        return {
            b'\xa5\x06\xb7\x89': 'QMCv1 FLAC',
            b'\x8a\x0e\xe5': 'QMCv1 MP3',
            b'<\xb8': 'QMCv1 MP3',
            b'<\xb9': 'QMCv1 MP3',
            b'<\xb1': 'QMCv1 MP3',
            b'\x8c-\xb1\x99': 'QMCv1 OGG'
        }

    def __init__(self,
                 filething: utils.FileThing | None = None,
                 **kwargs
                 ) -> None:
        """读写 QQ 音乐 QMCv1 格式的文件。

        Args:
            filething (file): 源 QMCv1 文件的路径或文件对象；留空则视为创建一个空 QMCv1 文件
        Keyword Args:
            use_slower_cipher (bool): 使用更慢但更稳定的加/解密方式

        所有未知的关键字参数都会被忽略。
        """
        if bool():
            # 此分支中的代码永远都不会执行，这是为了避免 PyCharm 警告“缺少超类调用”
            # 实际上并不需要调用 super().__init__()
            super().__init__()

        use_slower_cipher: bool = kwargs.get('use_slower_cipher', False)
        if filething is None:
            self._raw = BytesIO()
            if use_slower_cipher:
                self._cipher: StaticMap | OldStaticMap = OldStaticMap()
            else:
                self._cipher: StaticMap | OldStaticMap = StaticMap()
            self._name: str | None = None
        else:
            self.load(filething, **kwargs)

    def load(self,
             filething: utils.FileThing,
             **kwargs
             ) -> None:
        """将一个 QMCv1 文件加载到当前 QMCv1 对象中。

        Args:
            filething (file): 源 QMCv1 文件的路径或文件对象
        Keyword Args:
            use_slower_cipher (bool): 使用更慢但更稳定的加/解密方式
        Raises:
            FileTypeMismatchError: ``filething`` 不是一个 QMCv1 格式文件

        所有未知的关键字参数都会被忽略。
        """
        use_slower_cipher: bool = kwargs.get('use_slower_cipher', False)

        if utils.is_filepath(filething):
            fileobj: IO[bytes] = open(filething, 'rb')  # type: ignore
            self._name: str | None = fileobj.name
        else:
            fileobj: IO[bytes] = filething  # type: ignore
            self._name: str | None = getattr(fileobj, 'name', None)
            utils.verify_fileobj_readable(fileobj, bytes)
            utils.verify_fileobj_seekable(fileobj)

        self._raw = BytesIO(fileobj.read())
        if utils.is_filepath(filething):
            fileobj.close()

        if use_slower_cipher:
            self._cipher: StaticMap | OldStaticMap = OldStaticMap()
        else:
            self._cipher: StaticMap | OldStaticMap = StaticMap()

    def save(self,
             filething: utils.FileThing | None = None,
             **kwargs
             ) -> None:
        """将当前 QMCv1 对象保存为一个 QMCv1 格式文件。

        Args:
            filething (file): 目标 QMCv1 文件的路径或文件对象；
                留空则尝试使用 ``self.name``；如果两者都为空，抛出 ``ValueError``
        Raises:
            ValueError: 同时缺少参数 ``filething`` 和属性 ``self.name``

        所有未知的关键字参数都会被忽略。
        """
        super().save(filething, **kwargs)

    @property
    def cipher(self) -> StaticMap | OldStaticMap:
        return self._cipher


class QMCv2(Crypter):
    """读取 QQ 音乐 QMCv2 格式的文件。

    读取：

    >>> qmcv2file = QMCv2('./test.mflac')
    >>> data = qmcv2file.read()
    >>>
    
    读取没有可用密钥的 QMCv2 格式文件：
    
    >>> try:
    ...     qmcv2file_nokey = QMCv2('./test_nokey.mflac')
    ... except UnsupportedFileType:
    ...     qmcv2file_nokey = QMCv2('./test_nokey.flac', try_fallback=True)
    ...
    >>>

    写入：

    >>> qmcv2file.write(b'Writted bytes')

    创建空文件并写入：

    >>> empty_qmcv2file = QMCv2()
    >>> with open('source.flac', 'rb') as f:
    ...     empty_qmcv2file.write(f.read())
    >>>

    保存为 QMCv2 文件：

    >>> empty_qmcv2file.save('target.mflac')
    >>> empty_qmcv2file.save('target.mflac0', use_qtag=True, songid=114514810)
    >>>
    """

    @staticmethod
    def unsupported_file_tailer() -> dict[bytes, str]:
        return {
            b'\x25\x02\x00\x00': 'QMCv2 with new key format',
            b'STag': 'QMCv2 without key'
        }

    def __init__(self,
                 filething: utils.FileThing | None = None,
                 **kwargs
                 ) -> None:
        """读写 QQ 音乐 QMCv2 格式的文件。

        部分 QMCv2 格式文件因为没有可用的密钥，目前无法读写，
        可从它们末尾四个字节的十六进制值判断：

        - ``25 02 00 00``：来自版本 18.57 及以上的 QQ 音乐 PC 客户端，密钥使用了新的加密方案
        - ``53 54 61 67`` （``STag``）：来自版本 11.5.5 及以上的 QQ 音乐 Android 客户端，没有内置密钥

        可以尝试使用后备方案（指定 ``try_fallback=True``）读取这类无可用密钥的文件，
        但后备方案针对这些文件并不一定总是有效。

        Args:
            filething (file): 指向源文件的路径或文件对象；留空则视为创建一个空的 QMCv2 文件
        Keyword Args:
            key (bytes): 加/解密数据所需的密钥；留空则会随机生成一个；
                仅在 ``filething`` 为空时有效
            cipher_type (str): 加密类型，仅在 ``filething`` 为空时有效；
                支持：``dynamic_map``（默认值）、``rc4``；
            try_fallback (bool): 如果无法找到可用的密钥，是否尝试使用后备方案，
                默认为 False；仅在从 QMCv2 文件读取时有效
        Raises:
            ValueError: 为参数 ``cipher_type`` 指定了不支持的值

        所有未知的关键字参数都会被忽略。
        """
        if bool():
            # 此分支中的代码永远都不会执行，这是为了避免 PyCharm 警告“缺少超类调用”
            # 实际上并不需要调用 super().__init__()
            super().__init__()

        key: bytes | None = kwargs.get('key')
        cipher_type: Literal['dynamic_map', 'rc4'] = kwargs.get('cipher_type', 'dynamic_map')

        if filething is None:
            if cipher_type.lower() == 'dynamic_map':
                if key is None:
                    cipher_key = utils.gen_random_string(256).encode()
                else:
                    cipher_key = key
                self._cipher: DynamicMap | ModifiedRC4 | Key256Mask128 = DynamicMap(cipher_key)
            elif cipher_type.lower() == 'rc4':
                if key is None:
                    cipher_key = utils.gen_random_string(512).encode()
                else:
                    cipher_key = key
                self._cipher: DynamicMap | ModifiedRC4 | Key256Mask128 = ModifiedRC4(cipher_key)
            else:
                raise ValueError(f"'cipher_type' must be str 'dynamic_map' or 'rc4'")
            self._raw = BytesIO()
            self._name = None
            self._songid: int | None = None
            self._qtag_unknown: bytes | None = None
        else:
            self.load(filething, **kwargs)

    @classmethod
    def get_qtag(cls, fileobj: IO[bytes]) -> tuple[int, bytes, int, bytes]:
        fileobj.seek(-8, 2)
        raw_qtag_len = int.from_bytes(fileobj.read(4), 'big')

        audio_len = fileobj.seek(-(raw_qtag_len + 8), 2)
        raw_qtag = fileobj.read(raw_qtag_len)

        qtag: list[bytes] = raw_qtag.split(b',')
        if len(qtag) != 3:
            raise InvalidDataError('invalid QTag data')

        raw_key, songid, unknown = qtag

        return audio_len, raw_key, int(songid), unknown

    def load(self,
             filething: utils.FileThing,
             **kwargs
             ) -> None:
        """将一个 QMCv2 文件加载到当前 QMCv2 对象中。

        在此过程中需要先找到文件中可用的密钥：

        如果找到了可用的密钥，那么给 ``__init__()`` 传递的 ``key``
        和 ``cipher_type`` 参数将会被探测到的密钥和加密算法类型取代。

        如果没有可用的密钥，可加上参数 ``try_fallback=True``使用后备方案再次尝试。

        后备方案针对无可用密钥的文件并不一定总是有效。

        Args:
            filething (file): 源 QMCv2 文件的路径或文件对象
        Keyword Args:
            try_fallback (bool): 如果无法找到可用的密钥，是否尝试使用后备方案，
            默认为 False
        Raises:
            FileTypeMismatchError: ``filething`` 不是一个 QMCv2 格式文件
            UnsupportedFileType: ``filething`` 是一个 QMCv2 文件，但其格式不受支持

        所有未知的关键字参数都会被忽略。
        """
        try_fallback: bool = kwargs.get('try_fallback', False)

        if utils.is_filepath(filething):
            fileobj: IO[bytes] = open(filething, 'rb')  # type: ignore
            self._name: str | None = fileobj.name
        else:
            fileobj: IO[bytes] = filething  # type: ignore
            self._name: str | None = getattr(fileobj, 'name', None)
            utils.verify_fileobj_readable(fileobj, bytes)
            utils.verify_fileobj_seekable(fileobj)

        fileobj.seek(-4, 2)
        tail = fileobj.read(4)
        if tail in self.unsupported_file_tailer():
            if try_fallback:
                if tail == b'\x25\x02\x00\x00':
                    audio_len = fileobj.seek(-(4 + int.from_bytes(tail, 'little')), 2)
                else:
                    audio_len = fileobj.seek(-4, 2)
                b64encoded_ciphered_keydata: bytes | None = keyutils.find_mflac_mask(fileobj) or keyutils.find_mgg_mask(fileobj)
                songid = None
                unknown = None
                if not b64encoded_ciphered_keydata:
                    raise UnsupportedFileType(f'all attempt of decrypt failed: '
                                              f'{self.unsupported_file_tailer()[tail]}'
                                              )
            else:
                raise UnsupportedFileType(f'unsupported QMCv2 format: '
                                          f'{self.unsupported_file_tailer()[tail]}'
                                          )
        elif tail == b'QTag':
            audio_len, b64encoded_ciphered_keydata, songid, unknown = self.get_qtag(fileobj)
        else:
            fileobj.seek(-4, 2)
            raw_key_len = int.from_bytes(fileobj.read(4), 'little')
            if 0 < raw_key_len <= 0x300:
                audio_len = fileobj.seek(-(4 + raw_key_len), 2)
                b64encoded_ciphered_keydata = fileobj.read(raw_key_len)
                songid = None
                unknown = None
            else:
                raise FileTypeMismatchError('not a QMCv2 file: unknown file tail or key not found')

        if tail in self.unsupported_file_tailer() and try_fallback:
            self._cipher: DynamicMap | ModifiedRC4 | Key256Mask128 = Key256Mask128(b64encoded_ciphered_keydata)
        else:
            key = keyutils.QMCv2_key_decrypt(b64encoded_ciphered_keydata)
            if 0 < len(key) < 300:
                self._cipher: DynamicMap | ModifiedRC4 | Key256Mask128 = DynamicMap(key)
            else:
                self._cipher: DynamicMap | ModifiedRC4 | Key256Mask128 = ModifiedRC4(key)

        fileobj.seek(0, 0)
        self._raw = BytesIO(fileobj.read(audio_len))

        self._songid = songid
        self._qtag_unknown = unknown

    def save(self,
             filething: utils.FileThing | None = None,
             **kwargs
             ) -> None:
        """将当前 QMCv2 对象保存为一个 QMCv2 格式文件。

        Args:
            filething (file): 目标 QMCv2 文件的路径或文件对象；
                留空则尝试使用 ``self.name``；如果两者都为空，抛出 ``ValueError``
        Keyword Args:
            use_qtag (bool): 是否在输出的 QMCv2 文件中写入 QTag，默认为 False
            songid (int): QTag 中的歌曲 ID，可以留空；仅在 ``use_qtag=True`` 时有效
        Raises:
            ValueError: 同时缺少参数 ``filething`` 和属性 ``self.name``

        所有未知的关键字参数都会被忽略。
        """
        use_qtag: bool = kwargs.get('use_qtag', False)

        encoded_encrypted_keydata = keyutils.QMCv2_key_encrypt(self._cipher.key)

        if use_qtag:
            songid: int | None = kwargs.get('songid', self._songid)
            if songid is None:
                songid = 0
            qtag_unknown_value = 2 if self._qtag_unknown is None else self._qtag_unknown
            qtag = b','.join([
                encoded_encrypted_keydata,
                str(songid).encode(),
                str(qtag_unknown_value).encode()]
            )
            qtag_size = len(qtag).to_bytes(4, 'big')
            additionals = qtag + qtag_size + b'QTag'
        else:
            encoded_encrypted_keydata_size = len(encoded_encrypted_keydata).to_bytes(4, 'little')
            additionals = encoded_encrypted_keydata + encoded_encrypted_keydata_size

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

        self._raw.seek(0, 0)
        fileobj.write(self._raw.read())
        fileobj.write(additionals)
        if utils.is_filepath(filething):
            fileobj.close()

    @property
    def cipher(self) -> DynamicMap | ModifiedRC4 | Key256Mask128:
        return self._cipher

    @property
    def songid(self) -> int | None:
        return self._songid

    @property
    def qtag_unknown_value(self) -> bytes | None:
        return self._qtag_unknown
