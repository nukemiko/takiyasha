from __future__ import annotations


class TakiyashaException(Exception):
    pass


class DecryptException(TakiyashaException):
    pass


class FileTypeMismatchError(TakiyashaException):
    pass


class UnsupportedFileType(TakiyashaException):
    pass


class InvalidDataError(DecryptException):
    pass


class ValidationError(DecryptException):
    pass
