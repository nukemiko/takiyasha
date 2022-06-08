from __future__ import annotations

import os
from pathlib import Path
from typing import Generator, IO, Literal

from . import utils
from libtakiyasha import openfile, SupportsCrypter
from libtakiyasha.sniff import sniff_audio_file


def gen_pending_paths(srcfilepaths: list[Path],
                      destdirpath: Path | None = None,
                      recursive: bool = False,
                      ) -> Generator[tuple[Path, Path], None, None]:
    def get_destdirpath(srcfilepath_: Path):
        if destdirpath is None:
            return srcfilepath_.parent
        else:
            return destdirpath

    # 如果 destdirpath 不为 None，且不存在或不是目录，立即引发异常以退出
    if destdirpath is not None:
        if not destdirpath.exists():
            utils.fatal(f"输出路径 '{destdirpath}' 不存在，退出")
            raise FileNotFoundError
        if not destdirpath.is_dir():
            utils.fatal(f"输出路径 '{destdirpath}' 不是目录，退出")
            raise NotADirectoryError

    # 去除 srcfilepaths 中经过解析后的重复路径
    # _ = {p.resolve() for p in srcfilepaths}
    # srcfilepaths = sorted(list(_))

    for srcfilepath in srcfilepaths:
        if srcfilepath.exists():
            if srcfilepath.is_file():
                yield srcfilepath, get_destdirpath(srcfilepath)
            elif srcfilepath.is_dir():
                if recursive:
                    for subdir_srcfilepath in sorted(list(srcfilepath.iterdir())):
                        if subdir_srcfilepath.is_file():
                            yield subdir_srcfilepath, get_destdirpath(subdir_srcfilepath)
                        elif subdir_srcfilepath.is_dir():
                            utils.warn(f"跳过输入路径中的子目录 '{subdir_srcfilepath}'")
                        else:
                            utils.warn(f"跳过输入路径中未知状态的子路径 '{subdir_srcfilepath}'")
                else:
                    utils.warn(f"跳过输入路径中的目录 '{srcfilepath}'")
            else:
                utils.warn(f"跳过未知状态的输入路径 '{srcfilepath}'")
        else:
            utils.warn(f"跳过不存在的输入路径 '{srcfilepath}'")


def probe(srcfilepath: Path,
          **kwargs
          ) -> tuple[SupportsCrypter, str] | None:
    try:
        crypter = openfile(srcfilepath, **kwargs)
    except Exception as exc:
        utils.error(f"探测输入文件 '{srcfilepath}' 的加密类型时："
                    f"{type(exc).__name__}: {exc}"
                    )
        return
    else:
        if not crypter:
            return

    if crypter.seekable():
        crypter.seek(0, 0)

    try:
        destfilename_ext = sniff_audio_file(crypter)
    except Exception as exc:
        utils.error(f"探测输入文件 '{srcfilepath}' 的输出文件格式时："
                    f"{type(exc).__name__}: {exc}"
                    )
        return
    else:
        if not destfilename_ext:
            utils.warn(f"输入文件 '{srcfilepath}' 的输出文件格式未知")
            destfilename_ext = 'unknown'

    if crypter.seekable():
        crypter.seek(0, 0)

    return crypter, destfilename_ext


def decrypt(srcfilepath: Path,
            destfilepath: Path,
            crypter: SupportsCrypter
            ) -> IO[bytes] | None:
    # 以排他读写模式创建输出文件
    try:
        destfile = open(destfilepath, 'x+b')
    except FileExistsError:  # 输出文件路径已存在时应当引发的异常
        utils.error(f"输出文件已存在：'{destfilepath}'")
        return
    except Exception as exc:
        utils.error(f"打开输出文件 '{destfilepath}' 时："
                    f"{type(exc).__name__}: {exc}"
                    )
        return

    # 确保 crypter 的指针处于开头
    if crypter.seekable():
        crypter.seek(0, 0)

    # 从 crypter 中读取（解密）数据，并写入 destfile
    try:
        destfile.write(crypter.read())
    except Exception as exc:
        # 捕获到任何异常时，关闭和删除 destfile
        utils.error(f"解密输入文件 '{srcfilepath}' 到 '{destfilepath}' 时："
                    f"{type(exc).__name__}: {exc}"
                    )
        destfile.close()
        os.remove(destfilepath)
        return
    finally:  # 必要的收尾措施
        crypter.close()

    # 如果流程完整地走到了这里，将 destfile 的指针置零，然后返回 destfile
    destfile.seek(0, 0)
    return destfile


def mainflow(srcfilepath: Path,
             destdirpath: Path,
             probe_only: bool = False,
             with_tag: bool = True,
             search_tag: bool = True,
             search_tag_from: Literal['auto', 'cloudmusic', 'qqmusic'] = 'auto',
             status_pool: list[bool] | None = None,
             **kwargs
             ) -> None:
    def return_handler(status: bool):
        if status_pool is not None:
            status_pool.append(status)

    # 探测加密类型、预期输出格式，获取 crypter
    probe_result = probe(srcfilepath=srcfilepath,
                         **kwargs
                         )
    if probe_result:  # 有探测结果
        crypter, destfilepath_ext = probe_result
        if probe_only:  # 使用者要求仅探测不解密
            utils.info(f"输入文件 [{utils.get_encryption_name(crypter)}] '{srcfilepath}'，"
                       f"输出文件格式为 {destfilepath_ext.upper()}"
                       )
            return_handler(True)
            return
        else:
            if crypter.seekable():
                crypter.seek(0, 0)
            destfilepath = destdirpath / (srcfilepath.stem + '.' + destfilepath_ext)
            utils.info(f"输入文件 [{utils.get_encryption_name(crypter)}] '{srcfilepath}'，"
                       f"输出文件 '{destfilepath}'"
                       )
    else:  # 没有探测结果，说明文件不受支持
        utils.error(f"不支持输入文件 '{srcfilepath}'。"
                    f"或许你忘了添加 '-f, --try-fallback' 选项？"
                    )
        return_handler(False)
        return

    # 解密过程
    destfile = decrypt(srcfilepath, destfilepath, crypter)
    if destfile:
        utils.info(f"解密完成：'{srcfilepath}' -> '{destfilepath}'")
    else:  # destfile 为 None，说明解密过程中出错
        return_handler(False)
        return

    # 补充标签信息
    if with_tag:
        bool(search_tag)
        bool(search_tag_from)
        utils.warn('补充标签信息的功能尚未实现，敬请期待')

    return_handler(True)
    return
