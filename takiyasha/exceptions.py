class DecryptionException(Exception):
    pass


class DecryptFailed(DecryptionException):
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


class CLIException(Exception):
    pass


class CLIError(CLIException):
    pass
