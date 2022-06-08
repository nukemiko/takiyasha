from __future__ import annotations

import multiprocessing as mp
import sys
from argparse import ArgumentError
from pathlib import Path

from . import utils
from .argdefs import ap
from .core import gen_pending_paths, mainflow


def main() -> int:
    if sys.platform.startswith('linux'):
        mp.set_start_method('fork')
    else:
        mp.set_start_method('spawn')

    try:
        openfile_kwargs = vars(ap.parse_args())
    except ArgumentError as exc:
        utils.fatal(f'无法解析命令行参数：{exc}')
        return 2

    srcfilepaths: list[Path] = openfile_kwargs.pop('srcfilepaths')
    destdirpath_: Path = openfile_kwargs.pop('destdirpath')
    destdirpath_is_srcfiledirpath: bool = openfile_kwargs.pop('destdirpath_is_srcfiledirpath')
    recursive: bool = openfile_kwargs.pop('recursive')
    enable_multiprocessing: bool = openfile_kwargs.pop('enable_multiprocessing')
    try_fallback: bool = openfile_kwargs.pop('try_fallback')
    probe_only: bool = openfile_kwargs.pop('probe_only')
    keep_quiet: bool = openfile_kwargs.pop('keep_quiet')
    with_tag: bool = openfile_kwargs.pop('with_tag')
    search_tag: bool = openfile_kwargs.pop('search_tag')
    search_tag_from: str = openfile_kwargs.pop('search_tag_from')

    utils.DISABLE_PRINT_FUNCS = keep_quiet

    if try_fallback:
        openfile_kwargs.update({
            'try_fallback': True
        }
        )

    try:
        if destdirpath_is_srcfiledirpath:
            pending_paths: list[tuple[Path, Path]] = list(
                gen_pending_paths(srcfilepaths=srcfilepaths,
                                  destdirpath=None,
                                  recursive=recursive
                                  )
            )
        else:
            pending_paths: list[tuple[Path, Path]] = list(
                gen_pending_paths(srcfilepaths, destdirpath_, recursive)
            )
    except (FileNotFoundError, NotADirectoryError):
        return 1

    if len(pending_paths) == 0:
        utils.warn("未找到任何支持的输入文件。或许你忘了添加 '-r, --recursive' 选项？")
        return 0

    if enable_multiprocessing:
        utils.warn("您正处于并行处理模式，"
                   "这可能导致 CPU、RAM 等系统资源消耗急剧上升！"
                   )

        with mp.Manager() as mgr:
            status_pool: list[bool] = mgr.list()
            procs = []
            for srcfilepath_, destdirpath_ in pending_paths:
                mainflow_kwargs = {
                    'srcfilepath': srcfilepath_,
                    'destdirpath': destdirpath_,
                    'probe_only': probe_only,
                    'with_tag': with_tag,
                    'search_tag': search_tag,
                    'search_tag_from': search_tag_from,
                    'status_pool': status_pool
                }
                mainflow_kwargs.update(openfile_kwargs)

                p = mp.Process(target=mainflow, kwargs=mainflow_kwargs)
                p.start()
                procs.append(p)

            try:
                for p in procs:
                    p.join()
            except KeyboardInterrupt:
                utils.fatal('用户使用 Ctrl+C 或 SIGINT 终止了操作')
                for p in procs:
                    p.terminate()
                return 130

            if all(status_pool):
                utils.info('所有操作均已完成')
                return 0
            else:
                utils.info(f'有 {status_pool.count(False)} 个操作未能完成，但没有致命错误')
                return 0
    else:
        utils.warn("您添加了 '--np, --no-parallel' 选项，将不会使用并行处理进行解密，"
                   "这会增加您的等待时间"
                   )

        status_pool: list[bool] = []
        for srcfilepath_, destdirpath_ in pending_paths:
            mainflow_kwargs = {
                'srcfilepath': srcfilepath_,
                'destdirpath': destdirpath_,
                'probe_only': probe_only,
                'with_tag': with_tag,
                'search_tag': search_tag,
                'search_from': search_tag_from,
                'status_pool': status_pool
            }
            mainflow_kwargs.update(openfile_kwargs)

            try:
                mainflow(**mainflow_kwargs)
            except KeyboardInterrupt:
                utils.fatal('用户使用 Ctrl+C 或 SIGINT 终止了操作')
                return 130

        if all(status_pool):
            utils.info('所有操作均已完成')
            return 0
        else:
            utils.info(f'有 {status_pool.count(False)} 个操作未能完成，但没有致命错误')
            return 0
