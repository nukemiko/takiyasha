import os
from fnmatch import fnmatch
from typing import Optional

from .typehints import BytesType, PathType

SUPPORTED_FORMATS_PATTERNS: dict[str, list[str]] = {
    'NCM': ['*.ncm'],
    'QMC': ['*.qmc[023468]', '*.qmcflac', '*.qmcogg',
            '*.tkm',
            '*.mflac', '*.mflac[0]', '*.mgg', '*.mgg[01l]',
            '*.bkcmp3', '*.bkcm4a', '*.bkcflac', '*.bkcwav', '*.bkcape', '*.bkcogg', '*.bkcwma']
}

FILE_HEADER_FORMAT_MAP: dict[bytes, str] = {
    b'fLaC': 'flac',
    b'ID3': 'mp3',
    b'OggS': 'ogg',
    b'ftyp': 'm4a',
    b'0&\xb2u\x8ef\xcf\x11\xa6\xd9\x00\xaa\x00b\xcel': 'wma',
    b'RIFF': 'wav',
    b'\xff\xf1': 'aac',
    b'FRM8': 'dff'
}
FILE_FORMAT_HEADER_MAP: dict[str, bytes] = {
    v: k for k, v in FILE_HEADER_FORMAT_MAP.items()
}


def get_file_ext_by_header(data: BytesType) -> Optional[str]:
    for header, fmt in FILE_HEADER_FORMAT_MAP.items():
        if data.startswith(header):
            return fmt


def get_header_by_file_fmt(fmt: str) -> Optional[bytes]:
    fmt: str = fmt.removeprefix('.')
    return FILE_FORMAT_HEADER_MAP.get(fmt)


def get_file_ext(name: PathType) -> str:
    return os.path.splitext(name)[1]


def get_encryption_format(name: PathType) -> Optional[str]:
    for enctype, patterns in SUPPORTED_FORMATS_PATTERNS.items():
        for pattern in patterns:
            if fnmatch(name, pattern):
                return enctype
