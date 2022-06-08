from __future__ import annotations

__VERSION__ = '0.6.0.dev5'

import re
from typing import Type, Union

from . import utils
from .exceptions import TakiyashaException
from .ncm import NCM
from .ncmcache import NCMCache
from .qmc import QMCv1, QMCv2
from .sniff import sniff_audio_file

SupportsCrypter = Union[NCM, NCMCache, QMCv1, QMCv2]


def get_version() -> str:
    return __VERSION__


def extensions_crypters() -> dict[str, Type[SupportsCrypter]]:
    return {
        r'^\.qmc[\da-z]{1,4}$': QMCv1,
        r'^\.mflac[\da-z]?$': QMCv2,
        r'^\.mgg[\da-z]?$': QMCv2,
        r'^\.ncm$': NCM,
        r'^\.uc!$': NCMCache
    }


def choose_crypter(filename: utils.FilePath) -> Type[SupportsCrypter] | None:
    ext = utils.get_filename_ext(filename)

    for regex, crypter_cls in extensions_crypters().items():
        if re.search(regex, ext):
            return crypter_cls


def openfile(filething: utils.FileThing, probe_content: bool = True, **crypter_kwargs) -> SupportsCrypter | None:
    """返回一个 ``Crypter`` 对象，可通过其操作加密的音频文件。

    在返回 ``Crypter`` 对象之前，会先探测文件的加密格式：

        - 如果 ``filething`` 为路径，那么会根据文件扩展名判断加密格式；
            - 如果同时指定了 ``guess=True``，那么还会根据文件内容判断加密格式。

        - 如果``filething`` 为文件对象，则始终根据文件内容判断加密格式。

        - 如果始终无法判断文件属于哪一种已知加密格式，返回 ``None``。

    如果通过文件路径初始化新 ``Cipher`` 对象时，捕获了加/解密相关的异常
    （继承自 ``TakiyashaException``），也会直接返回 None。

    所有未知的关键字参数都会在 ``Crypter`` 实例初始化时，传递给它的 ``__init__()`` 方法。

    Args:
        filething (file): 指向源文件的路径或文件对象，必须可读、可跳转
        probe_content (file): 当 ``filething`` 为路径时，是否根据文件内容判断加密格式，
            默认为 ``True``"""
    if utils.is_filepath(filething):
        crypter_cls = choose_crypter(filething)  # type: ignore
        if crypter_cls is None:
            crypter: SupportsCrypter | None = None
        else:
            crypter: SupportsCrypter | None = crypter_cls(filething, **crypter_kwargs)
    else:
        crypter: SupportsCrypter | None = None

    if crypter is None:
        if not utils.is_filepath(filething) or probe_content:
            for crypter_cls in tuple(set(extensions_crypters().values())):
                try:
                    crypter = crypter_cls(filething, **crypter_kwargs)
                except TakiyashaException:
                    pass
                else:
                    sniff_result = sniff_audio_file(crypter)
                    crypter.seek(0, 0)
                    if sniff_result:
                        return crypter
                    else:
                        crypter.close()
    else:
        return crypter
