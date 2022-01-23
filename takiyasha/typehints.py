from array import array
from mmap import mmap
from os import PathLike
from typing import Union

BytesType = Union[bytes, bytearray]
BytesType_tuple = bytes, bytearray

PathType = Union[str, bytes, PathLike[str, bytes]]
PathType_tuple = str, bytes, PathLike

WriteableBuffer = Union[bytearray, memoryview, array, mmap]
WriteableBuffer_tuple = bytearray, memoryview, array, mmap
