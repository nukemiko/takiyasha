from __future__ import annotations

from io import UnsupportedOperation
from os import path, PathLike
from random import choices as random_choices
from string import ascii_letters, digits as strdigits
from typing import Any, Callable, IO, Type, Union

FilePath = Union[str, bytes, PathLike]
FileObject = Union[IO[str], IO[bytes]]
FileThing = Union[FilePath, FileObject]


def is_filepath(obj: Any) -> bool:
    return isinstance(obj, (str, bytes)) or hasattr(obj, '__fspath__')


def verify_fileobj_readable(fileobj: IO,
                            iotype: Type[str | bytes] | None = None
                            ) -> None:
    if iotype is None:
        io_type: Type[str | bytes] = bytes
    else:
        io_type: Type[str | bytes] = iotype

    readable_attr: Callable[[], bool] | bool | None = getattr(fileobj, 'readable', None)
    if callable(readable_attr):
        is_readable: bool = readable_attr()
    elif isinstance(readable_attr, bool):
        is_readable: bool = readable_attr
    else:
        is_readable: bool = True

    if not is_readable:
        raise UnsupportedOperation('read')

    readresult: io_type = fileobj.read(0)
    if not isinstance(readresult, io_type):
        raise ValueError(f'result type of read() mismatch '
                         f'({type(readresult).__name__} != {io_type.__name__})'
                         )


def verify_fileobj_seekable(fileobj: IO) -> None:
    seekable_attr: Callable[[], bool] | bool | None = getattr(fileobj, 'seekable', None)
    if callable(seekable_attr):
        is_seekable: bool = seekable_attr()
    elif isinstance(seekable_attr, bool):
        is_seekable: bool = seekable_attr
    else:
        is_seekable: bool = True

    if not is_seekable:
        raise UnsupportedOperation('seek')

    fileobj.seek(0, 1)


def verify_fileobj_writable(fileobj: IO,
                            iotype: Type[str | bytes] | None = None
                            ) -> None:
    if iotype is None:
        io_type: Type[str | bytes] = bytes
    else:
        io_type: Type[str | bytes] = iotype

    writable_attr: Callable[[], bool] | bool | None = getattr(fileobj, 'writable', None)
    if callable(writable_attr):
        is_writable: bool = writable_attr()
    elif isinstance(writable_attr, bool):
        is_writable: bool = writable_attr
    else:
        is_writable: bool = True

    if not is_writable:
        raise UnsupportedOperation('write')

    fileobj.write(io_type())


def bytesxor(term1: bytes, term2: bytes) -> bytes:
    segment1 = bytes(term1)
    segment2 = bytes(term2)

    if len(segment1) != len(segment2):
        raise ValueError('only byte strings of equal length can be xored')

    def xor():
        for b1, b2 in zip(segment1, segment2):
            yield b1 ^ b2

    return bytes(xor())


def gen_random_string(length: int,
                      recipe: str = strdigits + ascii_letters
                      ) -> str:
    return ''.join(random_choices(recipe, k=length))


def get_filename_ext(filename: FilePath) -> str:
    stem, ext = path.splitext(path.basename(filename))
    return str(ext).lower()
