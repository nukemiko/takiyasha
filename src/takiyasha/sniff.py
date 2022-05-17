from __future__ import annotations

import re
from typing import IO

__all__ = ['sniff_audio_file']


class _BitPaddedMixin(object):
    def as_str(self, width=4, minwidth=4):
        return self.to_str(self, self.bits, self.bigendian, width, minwidth)  # type: ignore

    @staticmethod
    def to_str(value, bits=7, bigendian=True, width=4, minwidth=4):
        mask = (1 << bits) - 1

        if width != -1:
            index = 0
            bytes_ = bytearray(width)
            try:
                while value:
                    bytes_[index] = value & mask
                    value >>= bits
                    index += 1
            except IndexError:
                raise ValueError('Value too wide (>%d bytes)' % width)
        else:
            # PCNT and POPM use growing integers
            # of at least 4 bytes (=minwidth) as counters.
            bytes_ = bytearray()
            append = bytes_.append
            while value:
                append(value & mask)
                value >>= bits
            bytes_ = bytes_.ljust(minwidth, b"\x00")

        if bigendian:
            bytes_.reverse()
        return bytes(bytes_)

    @staticmethod
    def has_valid_padding(value, bits=7):
        """Whether the padding bits are all zero"""

        assert bits <= 8

        mask = (((1 << (8 - bits)) - 1) << bits)

        if isinstance(value, int):
            while value:
                if value & mask:
                    return False
                value >>= 8
        elif isinstance(value, bytes):
            for byte in bytearray(value):
                if byte & mask:
                    return False
        else:
            raise TypeError

        return True


class BitPaddedInt(int, _BitPaddedMixin):
    def __new__(cls, value, bits=7, bigendian=True):
        mask = (1 << bits) - 1
        numeric_value = 0
        shift = 0

        if isinstance(value, int):
            if value < 0:
                raise ValueError
            while value:
                numeric_value += (value & mask) << shift
                value >>= 8
                shift += bits
        elif isinstance(value, bytes):
            if bigendian:
                value = reversed(value)
            for byte in bytearray(value):
                numeric_value += (byte & mask) << shift
                shift += bits
        else:
            raise TypeError

        self = int.__new__(BitPaddedInt, numeric_value)

        self.bits = bits  # type: ignore
        self.bigendian = bigendian  # type: ignore
        return self


def audio_file_headers() -> dict[bytes, str]:
    return {
        b'^fLaC': 'flac',
        b'^OggS': 'ogg',
        b'^TTA': 'tta',
        b'^MAC ': 'ape',
        b'^\xff[\xf2\xf3\xfb]': 'mp3',
        b'^\xff\xf1': 'aac',
        b'^FRM8': 'dff',
        b'^RIFF': 'wav',
        b'^0&\xb2u\x8ef\xcf\x11\xa6\xd9\x00\xaa\x00b\xcel': 'wma',
        b'^.{4}ftyp': 'm4a'
    }


def sniff_audio_file(fileobj: IO[bytes]) -> str | None:
    fileobj.seek(0, 0)
    header = fileobj.read(16)
    if header.startswith(b'ID3'):
        size = 10 + BitPaddedInt(header[6:10])
        fileobj.seek(size, 0)
        header = fileobj.read(16)

    for regex, ext in audio_file_headers().items():
        if re.search(regex, header):
            return ext
