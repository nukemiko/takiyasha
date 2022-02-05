from typing import Optional

from ..common import StreamCipher


class NoOperationStreamCipher(StreamCipher):
    """一个继承自 StreamCipher 类的密码实现。

    这个“密码”是为了保持接口一致性而存在的。无需密钥，并且 decrypt() 会原样返回任何传入数据。

    应当在源数据无需解密、但又需要保持接口一致性时使用。"""

    def __init__(self, key: Optional[bytes] = None):
        super().__init__(key)

    def decrypt(self, src: bytes, offset: int = 0) -> bytes:
        """原样返回源数据，不对数据做任何操作。

        Args:
            src: 需要“解密”（原样返回）的源数据。
            offset: 为了保持接口一致性而存在，为它指定的任何值都会被忽略。"""
        int(offset)
        return src
