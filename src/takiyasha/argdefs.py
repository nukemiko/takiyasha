from __future__ import annotations

import argparse
import sys
from pathlib import Path

from libtakiyasha import get_version
from .constants import DESCRIPTION, EPILOG, PROGNAME


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


ap = argparse.ArgumentParser(prog=PROGNAME,
                             add_help=False,
                             formatter_class=argparse.RawTextHelpFormatter,
                             description=DESCRIPTION,
                             epilog=EPILOG,
                             exit_on_error=False
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
                     help='不显示任何信息，程序退出即为完成'
                     )

decrypt_options = ap.add_argument_group(title='解密相关选项')
decrypt_options.add_argument('-f', '--try-fallback',
                             dest='try_fallback',
                             action='store_true',
                             help='针对部分支持的加密类型，在首次解密失败时，\n'
                                  '使用后备方案再次尝试（有几率成功）'
                             )

tag_options = ap.add_argument_group(title='标签信息和封面相关选项（目前没有作用）')
tag_options.add_argument('--notag',
                         dest='with_tag',
                         action='store_false',
                         help='为部分输出文件补上缺失的标签'
                         )
tag_options.add_argument('--avoid-search-tag',
                         dest='search_tag',
                         action='store_false',
                         help="不要从网络上查找缺失的标签；\n"
                              "仅在未添加 '--notag' 选项时有效"
                         )
tag_options.add_argument('--search-tag-from',
                         dest='search_tag_from',
                         action='store',
                         choices=('auto', 'cloudmusic', 'qqmusic'),
                         default='auto',
                         help="在哪里查找缺失的标签，默认为根据加密类型自动选择；\n"
                              "仅在未添加 '--notag' 和 '--avoid-search-tag' 选项时有效"
                         )
