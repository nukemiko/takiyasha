from __future__ import annotations

import multiprocessing as mp
import sys
from pathlib import Path
from time import sleep

from .argdefs import ap
from .core import gen_srcs_dsts, task
from .utils import print_stderr, print_stdout


def main() -> None:
    mp.set_start_method('spawn')

    openfile_kwargs = vars(ap.parse_args())

    srcpaths: list[Path] = openfile_kwargs.pop('srcpaths')
    destdir: Path = openfile_kwargs.pop('destdir')
    destdir_is_srcdir: bool = openfile_kwargs.pop('destdir_is_srcdir')
    recursive: bool = openfile_kwargs.pop('recursive')
    show_details: bool = openfile_kwargs.pop('show_details')
    enable_multiprocessing: bool = openfile_kwargs.pop('enable_multiprocessing')
    try_fallback: bool = openfile_kwargs.pop('try_fallback')
    dont_decrypt: bool = openfile_kwargs.pop('dont_decrypt')

    tasked_paths = gen_srcs_dsts(*srcpaths,
                                 destdir=destdir,
                                 destdir_is_srcdir=destdir_is_srcdir,
                                 recursive=recursive
                                 )

    if len(tasked_paths) == 0:
        print_stdout('错误：输入路径中没有任何受支持的文件')
        print_stdout("提示：如果输入路径中存在目录，您应当加上 '-r' 或 '--recursive' 选项")
        sys.exit(1)

    if not openfile_kwargs['probe_content']:
        print_stdout("警告：您添加了 '--faster' 选项")
        print_stdout('将会跳过文件内容，仅根据文件名判断加密类型')
        print_stdout('可能会导致部分文件无法识别和解密')

    fallback_params = {
        'try_fallback': True
    }
    if try_fallback:
        print_stdout("提示：您添加了 '-f' 或 '--try-fallback' 选项")
        print_stdout('将在单个文件首次解密失败时，使用旧方案再次尝试')
        print_stdout('（仅限部分支持的加密类型，且不保证成功）')
        openfile_kwargs.update(fallback_params)

    if dont_decrypt:
        print_stdout("提示：您添加了 '-t' 或 '--test' 选项")
        print_stdout('将仅测试输入文件是否受支持，如果不支持将会发出警告')
        print_stdout('不会解密任何输入文件，也不会产生任何输出文件')

    if enable_multiprocessing:
        print_stdout("提示：您添加了 '-p' 或 '--parallel' 选项")
        print_stdout('将会使用多进程并行处理所有输入文件')
        print_stdout('可能会消耗大量 CPU 和运行内存资源！')

        task_procs: list[mp.Process] = []
        for cursrcfile, curdstdir in tasked_paths:
            params = {
                'srcfile': cursrcfile,
                'destdir': curdstdir,
                'show_details': show_details,
                'dont_decrypt': dont_decrypt
            }
            params.update(openfile_kwargs)

            p = mp.Process(target=task, kwargs=params, name=str(cursrcfile))
            p.start()
            task_procs.append(p)

        try:
            while len(task_procs) > 0:
                sleep(0.001)
                for p in task_procs:
                    if not p.is_alive():
                        task_procs.remove(p)
                        break
        except KeyboardInterrupt:
            print()
            print_stderr('过程被用户终止')
            for p in task_procs:
                p.kill()
            sys.exit(130)
        else:
            if not dont_decrypt:
                print_stdout('所有文件均已解密完毕')
            sys.exit()
    else:
        try:
            for cursrcfile, curdstdir in tasked_paths:
                params = {
                    'srcfile': cursrcfile,
                    'destdir': curdstdir,
                    'show_details': show_details,
                    'dont_decrypt': dont_decrypt
                }
                params.update(openfile_kwargs)

                task(**params)
        except KeyboardInterrupt:
            print()
            print_stderr('过程被用户终止')
            sys.exit(130)
        else:
            if not dont_decrypt:
                print_stdout('所有文件均已解密完毕')
            sys.exit()
