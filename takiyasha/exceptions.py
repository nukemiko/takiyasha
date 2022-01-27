class DecryptionException(Exception):
    pass


class DecryptionError(DecryptionException):
    pass


class ValidateFailed(DecryptionException):
    pass


class CipherException(Exception):
    pass


class CipherGenerationException(CipherException):
    pass


class CipherGenerationError(CipherGenerationException):
    pass
