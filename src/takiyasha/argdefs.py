from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .constants import DESCRIPTION, EPILOG, PROGNAME, __VERSION__


class ShowSupportedFormatsAndExit(argparse.Action):
    @staticmethod
    def show() -> None:
        print('目前支持的加密类型（使用正则表达式表示）：\n\n'
              '    NCM:   *.ncm *.uc!\n'
              '    QMCv1: *.qmc[0-9] *.qmcflac *.qmcogg *.qmcra\n'
              '    QMCv2: *.mflac[0-9a-zA-Z]? *.mgg[0-9a-zA-Z]?'
              )

    def __call__(self, parser, namespace, values, option_string=None):
        self.show()
        sys.exit()


try:
    ap = argparse.ArgumentParser(prog=PROGNAME,
                                 add_help=False,
                                 formatter_class=argparse.RawTextHelpFormatter,
                                 description=DESCRIPTION,
                                 epilog=EPILOG,
                                 exit_on_error=False
                                 )
except TypeError:
    ap = argparse.ArgumentParser(prog=PROGNAME,
                                 add_help=False,
                                 formatter_class=argparse.RawTextHelpFormatter,
                                 description=DESCRIPTION,
                                 epilog=EPILOG
                                 )

positional_args = ap.add_argument_group(title='必要的位置参数')
positional_args.add_argument('srcfilepaths',
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
                          version=f'%(prog)s {__VERSION__}',
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
                             dest='destdirpath',
                             action='store',
                             type=Path,
                             default=Path.cwd(),
                             help="将所有输出文件放置在指定目录下；\n"
                                  "与 '--ds, --dest-source' 冲突"
                             )
destdir_options.add_argument('--ds', '--dest-source',
                             dest='destdirpath_is_srcfiledirpath',
                             action='store_true',
                             help="将每一个输出文件放置在源文件所在目录下；\n"
                                  "与 '-d, --dest' 冲突"
                             )
options.add_argument('-r', '--recursive',
                     action='store_true',
                     help='如果 PATH 中存在目录，那么递归处理目录下的文件\n'
                          '（不包括子目录）'
                     )
options.add_argument('--np', '--no-parallel',
                     dest='enable_multiprocessing',
                     action='store_false',
                     help='不使用并行模式'
                     )
options.add_argument('-t', '--test',
                     dest='probe_only',
                     action='store_true',
                     help='仅测试输入文件是否受支持，不进行解密'
                     )
options.add_argument('-q', '--quiet',
                     dest='keep_quiet',
                     action='store_true',
                     help='不显示任何信息，仅根据退出状态码表示运行结果'
                     )
tag_options = ap.add_argument_group(title='标签信息和封面相关选项')
tag_options.add_argument('--notag',
                         dest='with_tag',
                         action='store_false',
                         help='不要为输出文件补充缺失的标签'
                         )
tag_options.add_argument('--avoid-search-tag',
                         dest='search_tag',
                         action='store_false',
                         help="不要在网络上查找缺失的标签和封面信息；\n"
                              "仅在未添加 '--notag' 选项时有效"
                         )
