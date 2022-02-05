import os
import re
from fnmatch import fnmatch
from typing import IO, Optional

from .typehints import BytesType, PathType

SUPPORTED_FORMATS_PATTERNS: dict[str, list[str]] = {
    'ncm': ['*.ncm'],
    'qmc': ['*.qmc?', '*.qmcflac', '*.qmcogg',
            '*.tkm',
            '*.mflac', '*.mflac?', '*.mgg', '*.mgg?',
            '*.bkcmp3', '*.bkcm4a', '*.bkcflac', '*.bkcwav', '*.bkcape', '*.bkcogg', '*.bkcwma'],
    'tm': ['*.tm?'],
    'kgm': ['*.kgm', '*.kgma', '*.vpr']
}

AUDIO_FILE_HEADER_REGEX_FORMAT_MAP: dict[re.Pattern, str] = {
    re.compile(b'^fLaC'): 'flac',  # FLAC
    re.compile(b'^ID3.{,1021}fLaC'): 'flac',  # 嵌入 ID3v2 标签的 FLAC
    re.compile(b'^ID3'): 'mp3',  # 嵌入 ID3v2 标签的 MP3
    re.compile(b'^\xff[\xf2\xf3\xfb]'): 'mp3',  # 没有嵌入 ID3v2 标签的 MP3
    re.compile(b'^OggS'): 'ogg',  # OGG
    re.compile(b'^.{4}ftyp'): 'm4a',  # M4A
    re.compile(b'^0&\xb2u\x8ef\xcf\x11\xa6\xd9\x00\xaa\x00b\xcel'): 'wma',  # WMA
    re.compile(b'^\xff\xf1'): 'aac',  # AAC
    re.compile(b'^MAC '): 'ape',  # APE (Monkey's Audio)
    re.compile(b'^FRM8'): 'dff'  # DSDIFF
}
IMAGE_FILE_HEADER_REGEX_MIME_MAP: dict[re.Pattern, str] = {
    re.compile(b'^\x89PNG\r\n\x1a\n'): 'image/png',
    re.compile(b'^\xff\xd8\xff[\xdb\xe0\xe1\xee]'): 'image/jpeg',
    re.compile(b'^BM'): 'image/bmp',
    re.compile(b'^[\x49\x4d]{2}[\x2a\x00]{2}'): 'image/tiff'
}
IMAGE_FILE_HEADER_REGEX_FORMAT_MAP: dict[re.Pattern, str] = {
    re.compile(b'^\x89PNG\r\n\x1a\n'): 'png',
    re.compile(b'^\xff\xd8\xff[\xdb\xe0\xe1\xee]'): 'jpg',
    re.compile(b'^BM'): 'bmp',
    re.compile(b'^[\x49\x4d]{2}[\x2a\x00]{2}'): 'tiff'
}


def get_audio_format(data: bytes) -> Optional[str]:
    for header_regex, fmt in AUDIO_FILE_HEADER_REGEX_FORMAT_MAP.items():
        if header_regex.match(data):
            return fmt


def get_image_mimetype(data: bytes) -> Optional[str]:
    for header_regex, mime in IMAGE_FILE_HEADER_REGEX_MIME_MAP.items():
        if header_regex.match(data):
            return mime


def get_image_format(data: bytes) -> Optional[str]:
    for header_regex, fmt in IMAGE_FILE_HEADER_REGEX_FORMAT_MAP.items():
        if header_regex.match(data):
            return fmt


def get_file_ext(name: PathType) -> str:
    return os.path.splitext(name)[1]


def get_encryption_format(name: PathType) -> Optional[str]:
    for enctype, patterns in SUPPORTED_FORMATS_PATTERNS.items():
        for pattern in patterns:
            if fnmatch(name, pattern):
                return enctype


def is_fileobj(fileobj: IO[bytes]) -> bool:
    return not isinstance(fileobj, (str, bytes)) and not hasattr(fileobj, "__fspath__")


def raise_while_not_fileobj(
        fileobj: IO[bytes],
        *,
        readable=True,
        seekable=True,
        writable=False
) -> None:
    if readable:
        try:
            data = fileobj.read(0)
        except Exception:
            if not hasattr(fileobj, "read"):
                raise ValueError(f"{fileobj} not a valid file object")
            raise ValueError(f"cannot read from file object {fileobj}")

        if not isinstance(data, bytes):
            raise ValueError(f"file object {fileobj} not opened in binary mode")

    if seekable:
        try:
            fileobj.seek(0, os.SEEK_END)
        except Exception:
            if not hasattr(fileobj, "seek"):
                raise ValueError(f"{fileobj} not a valid file object")
            raise ValueError(f"cannot seek in file object {fileobj}")

    if writable:
        try:
            fileobj.write(b"")
        except Exception:
            if not hasattr(fileobj, "write"):
                raise ValueError(f"{fileobj} not a valid file object")
            raise ValueError(f"cannot write to file object {fileobj}")


def get_file_name_from_fileobj(fileobj: IO[bytes]):
    name = getattr(fileobj, 'name', '')
    if not isinstance(name, (str, bytes)):
        return str(name)
    return name


def xor_bytestrings(term1: BytesType, term2: BytesType) -> bytes:
    if len(term1) != len(term2):
        raise ValueError('Only byte strings of equal length can be xored')

    return bytes(b1 ^ b2 for b1, b2 in zip(term1, term2))
