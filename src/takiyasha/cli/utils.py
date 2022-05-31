from __future__ import annotations

import sys

from .constants import PROGNAME


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
