from typing import IO, Optional, Union

from .algorithms.common import Decrypter
from .algorithms.ncm import NCMDecrypter
from .algorithms.qmc import QMCDecrypter
from .typehints import PathType, PathType_tuple
from .utils import get_encryption_format, SUPPORTED_FORMATS_PATTERNS


def version() -> str:
    return '0.2.0'


_ENCTYPE_DECRYPTER_MAP = {
    'NCM': NCMDecrypter,
    'QMC': QMCDecrypter
}


def new_decrypter(
        filething: Union[PathType, IO[bytes]],
        encryption: str = None,
        **kwargs
) -> Decrypter:
    """Return a new Decrypter instance by the encryption format of file.
    
    :param filething: File path or file object.
    :param encryption: Encryption format of file.
    :param kwargs: All keyword arguments that need to be passed to open().
    :return: A new Decrypter instance."""
    if isinstance(filething, PathType_tuple):
        kwargs['file'] = filething
        kwargs['mode'] = 'rb'
        file: IO[bytes] = open(**kwargs)
    else:
        file: IO[bytes] = filething
    
    enctype: Optional[str] = None
    try:
        enctype: Optional[str] = get_encryption_format(file.name)
    except AttributeError:
        pass
    if encryption is None:
        if enctype is None:
            raise TypeError("failed to obtain encryption format, and 'encryption' is not specified")
    else:
        enctype: str = encryption
    enctype_orig: str = enctype
    enctype = enctype.upper()
    
    try:
        decrypter_class: Decrypter = _ENCTYPE_DECRYPTER_MAP[enctype]
    except KeyError:
        raise ValueError(f"unsupported encryption format '{enctype_orig}'")
    return decrypter_class.new(file)
