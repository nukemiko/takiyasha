class DecryptionException(Exception):
    pass


class DecryptionError(DecryptionException):
    pass


class UnsupportedDecryptionFormat(DecryptionException):
    pass


class DecryptionWarning(Warning):
    pass


class ValidateFailed(DecryptionException):
    pass


class CipherException(Exception):
    pass


class CipherGenerationException(CipherException):
    pass


class CipherGenerationError(CipherGenerationException):
    pass


class TagException(Exception):
    pass


class UnsupportedTagFormat(TagException):
    pass


class UnsupportedImageFormat(TagException):
    pass
