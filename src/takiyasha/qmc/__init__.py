from __future__ import annotations

from io import BytesIO
from typing import IO, Literal

from .ciphers.keycryption import QMCv2Key
from .ciphers.legacy import OldStaticMap
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

    写入：

    >>> qmcv1file.write(b'Writted bytes')

    创建、写入并保存：

    >>> new_qmcv1file = QMCv1()
    >>> with open('./source.flac', 'rb') as f:  # 写入未加密的文件数据
    ...     new_qmcv1file.write(f.read())
    >>> new_qmcv1file.save('./result.qmcflac')
    >>> """

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

    def __init__(self, filething: utils.FileThing | None = None, use_slower_cipher: bool = False) -> None:
        """读写 QQ 音乐 QMCv1 格式的文件。

        Args:
            filething (file): 源 QMCv1 文件的路径或文件对象；留空则视为创建一个空 QMCv1 文件
            use_slower_cipher (bool): 使用更慢但更稳定的加/解密方式
        """
        if bool():
            # 此分支中的代码永远都不会执行，这是为了避免 PyCharm 警告“缺少超类调用”
            # 实际上并不需要调用 super().__init__()
            super().__init__()

        if filething is None:
            self._raw = BytesIO()
            if use_slower_cipher:
                self._cipher: StaticMap | OldStaticMap = OldStaticMap()
            else:
                self._cipher: StaticMap | OldStaticMap = StaticMap()
            self._name: str | None = None
        else:
            self.load(filething, use_slower_cipher)

    def load(self, filething: utils.FileThing, use_slower_cipher: bool = False) -> None:
        """将一个 QMCv1 文件加载到当前 QMCv1 对象中。

        Args:
            filething (file): 源 QMCv1 文件的路径或文件对象
            use_slower_cipher (bool): 使用更慢但更稳定的加/解密方式
        Raises:
            FileTypeMismatchError: ``filething`` 不是一个 QMCv1 格式文件"""
        if utils.is_filepath(filething):
            fileobj: IO[bytes] = open(filething, 'rb')  # type: ignore
            self._name: str | None = fileobj.name
        else:
            fileobj: IO[bytes] = filething  # type: ignore
            self._name: str | None = getattr(fileobj, 'name', None)
            utils.verify_fileobj_readable(fileobj, bytes)
            utils.verify_fileobj_seekable(fileobj)

        cipher_audio_data = fileobj.read()
        if utils.is_filepath(filething):
            fileobj.close()
        for header in self.file_headers():
            if cipher_audio_data.startswith(header):
                self._raw = BytesIO(cipher_audio_data)
                break
        else:
            raise FileTypeMismatchError('not a QMCv1 file: bad file header')

        if use_slower_cipher:
            self._cipher: StaticMap | OldStaticMap = OldStaticMap()
        else:
            self._cipher: StaticMap | OldStaticMap = StaticMap()

    def save(self, filething: utils.FileThing | None = None) -> None:
        """将当前 QMCv1 对象保存为一个 QMCv1 格式文件。

        Args:
            filething (file): 目标 QMCv1 文件的路径或文件对象；
                留空则尝试使用 ``self.name``；如果两者都为空，抛出 ``ValueError``
        Raises:
            ValueError: 同时缺少参数 ``filething`` 和属性 ``self.name``"""
        super().save(filething)

    @property
    def cipher(self) -> StaticMap | OldStaticMap:
        return self._cipher


class QMCv2(Crypter):
    """读取 QQ 音乐 QMCv2 格式的文件。

    读取：

    >>> qmcv2file = QMCv2('./test.mflac')
    >>> data = qmcv2file.read()

    写入：

    >>> qmcv2file.write(b'Writted bytes')

    创建空文件并写入：

    >>> empty_qmcv2file = QMCv2()
    >>> empty_qmcv2file.write(b'Writted bytes')
    >>>

    目前不支持保存到文件。
    """

    @staticmethod
    def unsupported_file_tailer() -> dict[bytes, str]:
        return {
            b'\x25\x02\x00\x00': 'QMCv2 with new key format',
            b'STag': 'QMCv2 without key'
        }

    def __init__(self,
                 filething: utils.FileThing | None = None,
                 key: bytes | None = None,
                 cipher_type: Literal['dynamic_map', 'rc4'] = 'dynamic_map',
                 try_legacy: bool = False
                 ) -> None:
        """读取 QQ 音乐 QMCv2 格式的文件。

        目前支持向 QMCv2 对象写入数据，但不支持保存为 QMCv2 格式的文件。

        部分 QMCv2 格式文件目前无法读写，可从它们末尾四个字节的十六进制值判断：

        - ``25 02 00 00``：来自版本 18.57 及以上的 QQ 音乐 PC 客户端，其密钥使用了新的加密方案
        - ``53 54 61 67`` （``STag``）：来自版本 11.5.5 及以上的 QQ 音乐 Android 客户端，没有内置密钥

        尽管如此，如果使用后备方案（指定 ``try_legacy=True``，等待实现），
        仍然有可能读取以上不支持的文件。

        Args:
            filething (file): 指向源文件的路径或文件对象；留空则视为创建一个空的 QMCv2 文件
            key (bytes): 加/解密数据所需的密钥；留空则会随机创建一个；仅在 ``filething`` 为空时有效
            cipher_type (str): 加密类型，可选值：``dynamic_map``、``rc4``；仅在 ``filething`` 为空时有效
            try_legacy (bool): 如果无法找到可用的密钥，是否尝试使用后备方案，默认为 False
        Raises:
            ValueError: 为参数 ``cipher_type`` 指定了不支持的值
        """
        if bool():
            # 此分支中的代码永远都不会执行，这是为了避免 PyCharm 警告“缺少超类调用”
            # 实际上并不需要调用 super().__init__()
            super().__init__()

        if filething is None:
            if cipher_type.lower() == 'dynamic_map':
                if key is None:
                    cipher_key = utils.gen_random_string(256).encode()
                # elif len(key) != 256:
                #     raise ValueError(f'key length is too short (should be 256, got {len(key)}')
                else:
                    cipher_key = key
                self._cipher: DynamicMap | ModifiedRC4 = DynamicMap(cipher_key)
            elif cipher_type.lower() == 'rc4':
                if key is None:
                    cipher_key = utils.gen_random_string(512).encode()
                # elif len(key) != 512:
                #     raise ValueError(f'key length is too short (should be 512, got {len(key)}')
                else:
                    cipher_key = key
                self._cipher: DynamicMap | ModifiedRC4 = ModifiedRC4(cipher_key)
            else:
                raise ValueError(f"'cipher_type' must be str 'dynamic_map' or 'rc4'")
            self._raw = BytesIO()
            self._name = None
            self._songid: int | None = None
            self._qtag_unknown: bytes | None = None
        else:
            self.load(filething, try_legacy)

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

    def load(self, filething: utils.FileThing, try_legacy: bool = False) -> None:
        """将一个 QMCv2 文件加载到当前 QMCv2 对象中。

        Args:
            filething (file): 源 QMCv2 文件的路径或文件对象
            try_legacy (bool): 如果无法找到可用的密钥，是否尝试使用后备方案，默认为 False
        Raises:
            FileTypeMismatchError: ``filething`` 不是一个 QMCv2 格式文件
            UnsupportedFileType: ``filething`` 是一个 QMCv2 文件，但其格式不受支持
        """
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
            if try_legacy:
                raise NotImplementedError('coming soon: use legacy method as fallback')
            raise UnsupportedFileType(f'unsupported qmc file format: {self.unsupported_file_tailer()[tail]}')
        elif tail == b'QTag':
            audio_len, raw_keydata, songid, unknown = self.get_qtag(fileobj)
        else:
            fileobj.seek(-4, 2)
            raw_key_len = int.from_bytes(fileobj.read(4), 'little')
            if 0 < raw_key_len <= 0x300:
                audio_len = fileobj.seek(-(4 + raw_key_len), 2)
                raw_keydata = fileobj.read(raw_key_len)
                songid = None
                unknown = None
            else:
                raise FileTypeMismatchError('not a QMCv2 file: unknown file tail and key not found')

        key = QMCv2Key().decrypt(raw_keydata)
        if 0 < len(key) < 300:
            self._cipher: DynamicMap | ModifiedRC4 = DynamicMap(key)
        else:
            self._cipher: DynamicMap | ModifiedRC4 = ModifiedRC4(key)

        fileobj.seek(0, 0)
        self._raw = BytesIO(fileobj.read(audio_len))

        self._songid = songid
        self._qtag_unknown = unknown

    def save(self, filething: utils.FileThing | None = None) -> None:
        """将当前 QMCv2 对象保存为一个 QMCv2 格式文件。

        警告：目前不支持保存到文件；尝试调用本方法会引发 ``NotImplementedError``

        Args:
            filething (file): 目标 QMCv2 文件的路径或文件对象；
                留空则尝试使用 ``self.name``；如果两者都为空，抛出 ``ValueError``
        Raises:
            ValueError: 同时缺少参数 ``filething`` 和属性 ``self.name``
            NotImplementedError: 在调用本方法时引发；此异常将在未来加入功能后移除"""
        key = self._cipher.key
        bool(key)
        key_cipher = QMCv2Key()
        if not key_cipher.support_encrypt:
            raise NotImplementedError

    @property
    def cipher(self) -> DynamicMap | ModifiedRC4:
        return self._cipher

    @property
    def songid(self) -> int | None:
        return self._songid

    @property
    def qtag_unknown_value(self) -> bytes | None:
        return self._qtag_unknown
