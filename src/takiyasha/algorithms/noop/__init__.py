from typing import IO, Optional

from .ciphers import NoOperationStreamCipher
from ..common import Cipher, Decoder
from ...utils import get_audio_format


class NoOperationDecoder(Decoder):
    """一个继承自 Decoder 的解码器实现。

    这个“解码器”是为了接口一致性而存在的。输入的文件数据通过 read() 方法原样返回。

    应当在源文件无需处理、但又需要保持接口一致性时使用。"""

    @classmethod
    def _pre_create_instance(cls, file: IO[bytes]) -> tuple[bytes, Cipher, dict[str, ...]]:
        file.seek(0, 0)

        header_data: bytes = file.read(32)
        audio_fmt: Optional[str] = get_audio_format(header_data)

        file.seek(0, 0)

        return file.read(), NoOperationStreamCipher(), {'audio_format': audio_fmt}
