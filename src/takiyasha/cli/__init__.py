from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import UUID, uuid4

from .. import get_version, openfile
from ..sniff import sniff_audio_file

PROGNAME = Path(__file__).parent.parent.name
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
        sys.exit()


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
                             help="将所有输出文件放置在指定目录下；与 '--ds, --dest-source' 冲突"
                             )
destdir_options.add_argument('--ds', '--dest-source',
                             dest='destdir_is_srcdir',
                             action='store_true',
                             help="将每一个输出文件放置在源文件所在目录下；与 '-d, --dest' 冲突"
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
options.add_argument('-p', '--parallel',
                     dest='enable_multiprocessing',
                     action='store_true',
                     help='使用多进程并行解密输入文件（实验性功能）'
                     )
options.add_argument('-t', '--test',
                     dest='dont_decrypt',
                     action='store_true',
                     help='仅测试输入文件是否受支持，不进行解密'
                     )
decrypt_options = ap.add_argument_group(title='解密相关选项')
decrypt_options.add_argument('--faster',
                             dest='probe_content',
                             action='store_false',
                             help='跳过文件内容，仅根据文件名判断加密类型'
                             )
decrypt_options.add_argument('-f', '--try-fallback',
                             dest='try_fallback',
                             action='store_true',
                             help='针对部分支持的加密类型，在首次解密失败时，使用旧方案再次尝试（有几率成功）'
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
