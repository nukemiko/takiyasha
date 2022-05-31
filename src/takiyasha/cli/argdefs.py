from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .constants import DESCRIPTION, EPILOG, PROGNAME
from .. import get_version


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
