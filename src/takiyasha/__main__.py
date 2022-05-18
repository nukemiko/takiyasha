from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import UUID, uuid4

from takiyasha import get_version, openfile, sniff_audio_file

PROGNAME = Path(__file__).parent.name
DESCRIPTION = f'  {PROGNAME} - Python 版本的音乐解密工具'
EPILOG = f'{PROGNAME} 对输出数据的可用性（是否可以识别、播放等）不做任何保证。\n\n' \
         f'项目地址：https://github.com/nukemiko/takiyasha/tree/remaked'


class ShowSupportedFormatsAndExit(argparse.Action):
    @staticmethod
    def show() -> None:
        print('目前支持的加密类型（使用正则表达式表示）：\n\n'
              '    NCM:   *.ncm *.uc!\n'
              '    QMCv1: *.qmc[0-9] *.qmcflac *.qmcogg\n'
              '    QMCv2: *.mflac[0-9a-zA-Z]? *.mgg[0-9a-zA-Z]?'
              )

    def __call__(self, parser, namespace, values, option_string=None):
        self.show()
        exit()


ap = argparse.ArgumentParser(prog=PROGNAME,
                             add_help=False,
                             formatter_class=argparse.RawDescriptionHelpFormatter,
                             description=DESCRIPTION,
                             epilog=EPILOG
                             )
positional_args = ap.add_argument_group(title='必要的位置参数')
positional_args.add_argument('srcpaths',
                             metavar='PATH',
                             nargs='+',
                             type=Path,
                             help='源文件或目录的路径'
                             )
help_options = ap.add_argument_group(title='帮助信息')
help_options.add_argument('-h', '--help',
                          action='help',
                          help='显示帮助信息并退出'
                          )
help_options.add_argument('-V', '--version',
                          action='version',
                          version=f'%(prog)s {get_version()}',
                          help='显示版本信息并退出'
                          )
help_options.add_argument('--formats',
                          nargs=0,
                          action=ShowSupportedFormatsAndExit,
                          help='显示支持的加密类型，然后退出'
                          )
options = ap.add_argument_group(title='可选参数')
destdir_options = options.add_mutually_exclusive_group()
destdir_options.add_argument('-d', '--dest',
                             metavar='DESTPATH',
                             dest='destdir',
                             action='store',
                             type=Path,
                             default=Path.cwd(),
                             help='将输出文件放置在指定目录下；与“--ds, --dest-source”冲突'
                             )
destdir_options.add_argument('--ds', '--dest-source',
                             dest='destdir_is_srcdir',
                             action='store_true',
                             help='将输出文件放置在源文件所在目录下；与“-d, --dest”冲突'
                             )
options.add_argument('-r', '--recursive',
                     action='store_true',
                     help='如果 PATH 中存在目录，那么递归处理目录下的文件（不包括子目录）'
                     )
options.add_argument('-v', '--details',
                     dest='show_details',
                     action='store_true',
                     help='显示每一个输入文件的细节（加密类型、预期输出格式等）'
                     )
decrypt_options = ap.add_argument_group(title='解密相关选项')
decrypt_options.add_argument('-s', '--fast',
                             dest='detect_content',
                             action='store_false',
                             help='仅根据文件名判断文件类型'
                             )
decrypt_options.add_argument('--lf', '--use-legacy-as-fallback',
                             dest='legacy_fallback',
                             action='store_true',
                             help='针对 QMCv2 文件，在首次尝试失败时，使用旧方案再次尝试（有几率成功）'
                             )


def print_stderr(*values: object,
                 sep: str | None = None,
                 end: str | None = None,
                 flush: bool = False
                 ) -> None:
    print(f'[{PROGNAME}]', *values, sep=sep, end=end, flush=flush, file=sys.stderr)


def print_stdout(*values: object,
                 sep: str | None = None,
                 end: str | None = None,
                 flush: bool = False
                 ) -> None:
    print(f'[{PROGNAME}]', *values, sep=sep, end=end, flush=flush)


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
                exit(1)
            elif destdir.is_dir():
                return [(p, destdir) for p in filepaths]
            else:
                print_stdout(f"错误：输出路径 '{destdir}'：无法判断其状态")
                exit(1)
        else:
            print_stdout(f"错误：输出路径 '{destdir}'：路径不存在")
            exit(1)


def task(srcfile: Path, destdir: Path, show_details: bool, **kwargs) -> None:
    if not kwargs['detect_content']:
        print_stdout(f"提示：将仅通过文件名判断 '{srcfile}' 的加密类型")
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
            print(f"=============================================\n"
                  f"任务 ID：{task_uuid}\n"
                  f"输入文件：'{srcfile}'\n"
                  f"加密类型：{type(crypter).__name__} ({crypter.cipher.cipher_name()})\n"
                  f"预计输出格式：{audio_ext.upper()}\n"
                  f"输出到：'{destfile}'\n"
                  f"============================================="
                  )
        if destfile.exists():
            print_stdout(f"警告：'{destfile}'：路径已存在，跳过")
            return
        with open(destfile, 'wb') as f:
            f.write(crypter.read())
            if show_details:
                print_stdout(f"完成：{task_uuid} ('{srcfile}' -> '{destfile}')")
            else:
                print_stdout(f"完成：'{srcfile}' -> '{destfile}'")


if __name__ == '__main__':
    openfile_kwargs = vars(ap.parse_args())

    srcpaths: list[Path] = openfile_kwargs.pop('srcpaths')
    destdir: Path = openfile_kwargs.pop('destdir')
    destdir_is_srcdir: bool = openfile_kwargs.pop('destdir_is_srcdir')
    recursive: bool = openfile_kwargs.pop('recursive')
    show_details: bool = openfile_kwargs.pop('show_details')

    tasked_paths = gen_srcs_dsts(*srcpaths,
                                 destdir=destdir,
                                 destdir_is_srcdir=destdir_is_srcdir,
                                 recursive=recursive
                                 )

    for cursrcfile, curdstdir in tasked_paths:
        task(srcfile=cursrcfile,
             destdir=curdstdir,
             show_details=show_details,
             **openfile_kwargs
             )
