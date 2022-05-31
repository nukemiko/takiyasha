from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID, uuid4

from .utils import print_stdout
from .. import openfile
from ..sniff import sniff_audio_file


def gen_srcs_dsts(*srcpaths: Path,
                  destdir: Path,
                  destdir_is_srcdir: bool,
                  recursive: bool
                  ) -> list[tuple[Path, Path]]:
    filepaths: list[Path] = []
    for path in srcpaths:
        if not path.exists():
            print_stdout(f"警告：输入路径 '{path}'：路径不存在，跳过")
            continue
        if path.is_file():
            filepaths.append(path)
        elif path.is_dir():
            if recursive:
                filepaths.extend(p for p in path.iterdir() if p.is_file())
            else:
                print_stdout(f"警告：输入路径 '{path}'：是一个目录，跳过")
                continue
        else:
            print_stdout(f"警告：输入路径 '{path}'：无法判断其状态，跳过")
            continue

    filepaths.sort()

    if destdir_is_srcdir:
        return [(p, p.parent) for p in filepaths]
    else:
        if destdir.exists():
            if destdir.is_file():
                print_stdout(f"错误：输出路径 '{destdir}'：是一个文件")
                sys.exit(1)
            elif destdir.is_dir():
                return [(p, destdir) for p in filepaths]
            else:
                print_stdout(f"错误：输出路径 '{destdir}'：无法判断其状态")
                sys.exit(1)
        else:
            print_stdout(f"错误：输出路径 '{destdir}'：路径不存在")
            sys.exit(1)


def task(srcfile: Path, destdir: Path, show_details: bool, dont_decrypt: bool, **kwargs) -> None:
    try:
        crypter = openfile(srcfile, **kwargs)
    except Exception as exc:
        print_stdout(f"警告：未能解密 '{srcfile}'：'{exc}'，跳过")
        return
    else:
        if crypter is None:
            print_stdout(f"警告：'{srcfile}'：非已知加密类型，跳过")
            return

        audio_ext = sniff_audio_file(crypter)
        if not audio_ext:
            print_stdout(f"警告：'{srcfile}' 的解密结果未知")
            audio_ext = 'unknown'
        crypter.seek(0, 0)

        task_uuid: UUID = uuid4()
        destfile = destdir / (srcfile.stem + f'.{audio_ext}')
        if show_details:
            print_to_stdouts = [
                f"=============================================",
                f"任务 ID：{task_uuid}",
                f"输入文件：'{srcfile}'",
                f"加密类型：{type(crypter).__name__} ({crypter.cipher.cipher_name()})",
                f"预计输出格式：{audio_ext.upper()}",
                f"输出到：'{destfile}'",
                f"============================================="
            ]
            if dont_decrypt:
                del print_to_stdouts[-2]
                del print_to_stdouts[1]
            print('\n'.join(print_to_stdouts))

        if dont_decrypt:
            return

        if destfile.exists():
            print_stdout(f"警告：'{destfile}'：路径已存在，跳过")
            return
        with open(destfile, 'wb') as f:
            f.write(crypter.read())
            if show_details:
                print_stdout(f"完成：{task_uuid} ('{srcfile}' -> '{destfile}')")
            else:
                print_stdout(f"完成：'{srcfile}' -> '{destfile}'")
