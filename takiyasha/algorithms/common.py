from abc import ABCMeta, abstractmethod
from typing import Optional

from takiyasha.typehints import BytesType, BytesType_tuple


class Cipher(metaclass=ABCMeta):
    """The base class of the cipher class hierarchy.
    
    You cannot directly call it, because it is designed as a template
    for other ciphers.
    
    Subclasses that inherit from this class must implement the decrypt() method."""
    
    def __init__(self, key: Optional[BytesType]):
        """Initialize self. See help(type(self)) for accurate signature."""
        if key is None:
            self._key: Optional[bytes] = None
        elif isinstance(key, BytesType_tuple):
            self._key: Optional[bytes] = bytes(key)
        else:
            raise TypeError(f"'key' must be byte or bytearray, not {type(key).__name__}")
    
    @property
    def key(self) -> Optional[bytes]:
        return self._key
    
    @property
    def key_length(self) -> Optional[int]:
        if self._key is not None:
            key_len: Optional[int] = len(self._key)
        else:
            key_len: Optional[int] = None
        return key_len
    
    @abstractmethod
    def decrypt(self, src_data: BytesType, /):
        """Accept encrypted src_data and return the decrypted data."""
        pass
