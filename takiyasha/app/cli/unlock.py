from typing import Callable, IO, Optional

from ...algorithms.ncm import NCMDecrypter
from ...algorithms.qmc import QMCDecrypter
from ...exceptions import CLIError
from ...utils import get_file_ext_by_header


def noop_file(file: IO[bytes], audiofmt: str) -> tuple[bytes, str, dict[str, ...]]:
    file.seek(0, 0)
    
    return file.read(), audiofmt, {}


def unlock_ncm_file(file: IO[bytes]) -> tuple[bytes, str, dict[str, ...]]:
    file.seek(0, 0)
    decrypter: NCMDecrypter = NCMDecrypter.new(file)
    
    audiofmt: str = decrypter.audio_format
    if not audiofmt:
        raise CLIError(f"Failed to recongize decrypted audio format: '{file.name}'")
    metadata: dict[str, ...] = decrypter.metadata.copy()
    identifier: str = decrypter.identifier
    cover_data: bytes = decrypter.cover_data
    metadata['identifier'] = identifier
    metadata['cover_data'] = cover_data
    
    miscellaneous: dict[str, ...] = {'metadata': metadata}
    
    decrypter.reset_buffer_offset()
    
    return decrypter.read(), audiofmt, miscellaneous


def unlock_qmcv1_qmcv2_file(file: IO[bytes]) -> tuple[bytes, str, dict[str, ...]]:
    file.seek(0, 0)
    decrypter: QMCDecrypter = QMCDecrypter.new(file)
    
    audiofmt: str = decrypter.audio_format
    if not audiofmt:
        raise CLIError(f"Failed to recongize decrypted audio format, skip: '{file.name}'")
    songid: Optional[int] = None
    if decrypter.raw_metadata_extra:
        songid: int = decrypter.raw_metadata_extra[0]
    
    miscellaneous: dict[str, ...] = {'songid': songid}
    
    decrypter.reset_buffer_offset()
    
    return decrypter.read(), audiofmt, miscellaneous


ENCTYPE_DECRYPTER_MAP = {
    'NCM': unlock_ncm_file,
    'QMC': unlock_qmcv1_qmcv2_file
}


def unlock(filepath: str, encryption: str) -> tuple[bytes, str, dict[str, ...]]:
    file: IO[bytes] = open(filepath, 'rb')
    
    # check no-op
    fmt: Optional[str] = get_file_ext_by_header(file.read(32))
    if fmt:
        return noop_file(file, fmt)
    
    decrypt_method: Callable[[IO[bytes]], tuple[bytes, str, dict[str, ...]]] = ENCTYPE_DECRYPTER_MAP.get(encryption)
    if not decrypt_method:
        raise CLIError(f"Cannot find a suitable unlock method, skip: '{filepath}'")
    
    return decrypt_method(file)
