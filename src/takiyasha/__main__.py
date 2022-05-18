from __future__ import annotations

import multiprocessing as mp
from time import sleep

from .cli import *

if __name__ == '__main__':
    mp.set_start_method('spawn')
    openfile_kwargs = vars(ap.parse_args())

    srcpaths: list[Path] = openfile_kwargs.pop('srcpaths')
    destdir: Path = openfile_kwargs.pop('destdir')
    destdir_is_srcdir: bool = openfile_kwargs.pop('destdir_is_srcdir')
    recursive: bool = openfile_kwargs.pop('recursive')
    show_details: bool = openfile_kwargs.pop('show_details')
    enable_multiprocessing: bool = openfile_kwargs.pop('enable_multiprocessing')

    tasked_paths = gen_srcs_dsts(*srcpaths,
                                 destdir=destdir,
                                 destdir_is_srcdir=destdir_is_srcdir,
                                 recursive=recursive
                                 )

    if enable_multiprocessing:
        task_procs: list[mp.Process] = []
        for cursrcfile, curdstdir in tasked_paths:
            params = {
                'srcfile': cursrcfile,
                'destdir': curdstdir,
                'show_details': show_details,
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
            sys.exit()
    else:
        try:
            for cursrcfile, curdstdir in tasked_paths:
                params = {
                    'srcfile': cursrcfile,
                    'destdir': curdstdir,
                    'show_details': show_details,
                }
                params.update(openfile_kwargs)

                task(**params)
        except KeyboardInterrupt:
            print()
            print_stderr('过程被用户终止')
            sys.exit(130)
        else:
            sys.exit()
