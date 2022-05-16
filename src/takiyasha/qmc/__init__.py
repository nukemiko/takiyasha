from __future__ import annotations

from io import BytesIO

from .ciphers.legacy import OldStaticMap
from .ciphers.modern import StaticMap
from ..common import Crypter
from ..exceptions import FileTypeMismatchError
from ..utils import FileThing, is_filepath, verify_fileobj_readable, verify_fileobj_seekable


class QMCv1(Crypter):
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

    def __init__(self, filething: FileThing | None = None, use_slower_cipher: bool = False) -> None:
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

    def load(self, filething: FileThing, use_slower_cipher: bool = False) -> None:
        if is_filepath(filething):
            fileobj: IO[bytes] = open(filething, 'rb')  # type: ignore
            self._name: str | None = fileobj.name
        else:
            fileobj: IO[bytes] = filething  # type: ignore
            self._name: str | None = getattr(fileobj, 'name', None)
            verify_fileobj_readable(fileobj, bytes)
            verify_fileobj_seekable(fileobj)

        cipher_audio_data = fileobj.read()
        if is_filepath(filething):
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

    @property
    def cipher(self) -> StaticMap | OldStaticMap:
        return self._cipher
