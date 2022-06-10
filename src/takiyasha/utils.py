from __future__ import annotations

import sys

import colorama

from .constants import PROGNAME
from libtakiyasha import SupportsCrypter

DISABLE_PRINT_FUNCS: bool = False

colorama.init()


def print_stderr(*values: object,
                 sep: str | None = None,
                 end: str | None = None,
                 flush: bool = False,
                 header: str | None = None
                 ) -> None:
    topheader = f'[{colorama.Fore.CYAN}{PROGNAME}{colorama.Fore.RESET}]'
    if header:
        topheader += header
    if not DISABLE_PRINT_FUNCS:
        print(topheader, *values, sep=sep, end=end, flush=flush, file=sys.stderr)


def print_stdout(*values: object,
                 sep: str | None = None,
                 end: str | None = None,
                 flush: bool = False,
                 header: str | None = None
                 ) -> None:
    topheader = f'[{colorama.Fore.CYAN}{PROGNAME}{colorama.Fore.RESET}]'
    if header:
        topheader += header
    if not DISABLE_PRINT_FUNCS:
        print(topheader, *values, sep=sep, end=end, flush=flush)


# 在打印一般信息时使用
def info(*values: object,
         sep: str | None = None,
         end: str | None = None,
         flush: bool = False
         ) -> None:
    print_stderr(*values,
                 sep=sep,
                 end=end,
                 flush=flush,
                 header=f'[INFO]'
                 )


# 在警告使用者可能出现的情况时使用
def warn(*values: object,
         sep: str | None = None,
         end: str | None = None,
         flush: bool = False
         ) -> None:
    print_stderr(*values,
                 sep=sep,
                 end=end,
                 flush=flush,
                 header=f'[{colorama.Fore.YELLOW}WARN{colorama.Fore.RESET}]'
                 )


# 在单个文件的探测/解密过程中出错时使用
def error(*values: object,
          sep: str | None = None,
          end: str | None = None,
          flush: bool = False
          ) -> None:
    print_stderr(*values,
                 sep=sep,
                 end=end,
                 flush=flush,
                 header=f'[{colorama.Fore.RED}ERROR{colorama.Fore.RESET}]'
                 )


# 出现要使程序立即退出的致命错误时使用
def fatal(*values: object,
          sep: str | None = None,
          end: str | None = None,
          flush: bool = False
          ) -> None:
    if sep is None:
        sep = f' '
    if end is None:
        end = f'{colorama.Fore.RESET}{colorama.Back.RESET}\n'
    else:
        end = f'{colorama.Fore.RESET}{colorama.Back.RESET}{end}'
    print_stderr(colorama.Back.RED + colorama.Fore.WHITE + sep.join((str(_) for _ in values)),
                 end=end,
                 flush=flush,
                 header=f'[{colorama.Fore.LIGHTRED_EX}FATAL{colorama.Fore.RESET}]'
                 )


def get_encryption_name(crypter: SupportsCrypter) -> str:
    return f'{type(crypter).__name__} ({crypter.cipher.cipher_name()})'
