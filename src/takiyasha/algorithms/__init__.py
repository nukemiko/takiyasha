from typing import IO, Optional, Type, Union

from .common import Decoder
from .kgm import KGMFormatDecoder
from .ncm import NCMFormatDecoder
from .noop import NoOperationDecoder
from .qmc import QMCFormatDecoder
from ..exceptions import DecryptionError, UnsupportedDecryptionFormat, ValidateFailed
from ..typehints import PathType
from ..utils import (
    get_audio_format,
    get_encryption_format,
    get_file_name_from_fileobj,
    is_fileobj
)

_ENCRYPTIONS_DECODERS = {
    'ncm': NCMFormatDecoder,
    'qmc': QMCFormatDecoder,
    'kgm': KGMFormatDecoder
}


def get_decoder_class(encryption: str) -> Optional[Type[Decoder]]:
    if hasattr(encryption, 'lower'):
        encryption: str = encryption.lower()
    return _ENCRYPTIONS_DECODERS.get(encryption)


def new_decoder(filething: Union[PathType, IO[bytes]], enable_noop_decoder=False) -> Decoder:
    """根据文件的加密格式，生成并返回对应的解码器。

    如果输入的文件满足以下三个条件：

    - 无法判断输入文件的加密格式
    - 输入文件并非音频文件
    - 参数 `enable_noop_decoder` 设置为 `False`

    则会抛出 `UnsupportedDecryptionFormat` 异常。

    Args:
        filething: 文件路径或文件对象。
                   若为路径，指向的必须是可读取的文件；
                   若为文件对象，必须可读取且支持从任意位置读取。
        enable_noop_decoder: 是否将 `NoOperationDecoder` 作为后备解码器
    Returns:
        和文件加密格式对应的解码器
    Raises:
        UnsupportedDecryptionFormat: 无法判断输入文件的加密格式、输入文件并非音频文件，且参数 `enable_noop_decoder` 设置为 `False`"""
    if is_fileobj(filething):
        file_name: Optional[str] = get_file_name_from_fileobj(filething)
        encryption: Optional[str] = get_encryption_format(file_name)
        file_header: bytes = filething.read(32)
    else:
        file_name: Optional[str] = filething
        encryption: Optional[str] = get_encryption_format(file_name)
        with open(file_name, 'rb') as f:
            file_header: bytes = f.read(32)

    decoder_class: Type[Decoder] = get_decoder_class(encryption)
    if not decoder_class:
        if get_audio_format(file_header):
            decoder: Decoder = NoOperationDecoder.from_file(filething)
        else:
            for decoder_class in _ENCRYPTIONS_DECODERS.values():
                try:
                    decoder: Decoder = decoder_class.from_file(filething)
                except ValidateFailed:
                    pass
                except DecryptionError:
                    if decoder_class != KGMFormatDecoder:
                        raise
                else:
                    break
            else:
                if not enable_noop_decoder:
                    raise UnsupportedDecryptionFormat(
                        f"file '{file_name}' is in an unrecongized format"
                    )
                decoder: Decoder = NoOperationDecoder.from_file(filething)
    else:
        decoder: Decoder = decoder_class.from_file(filething)

    return decoder
