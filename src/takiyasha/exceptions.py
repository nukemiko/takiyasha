from __future__ import annotations


class TakiyashaException(Exception):
    pass


class DecryptException(TakiyashaException):
    pass


class FileTypeMismatchError(TakiyashaException):
    pass
