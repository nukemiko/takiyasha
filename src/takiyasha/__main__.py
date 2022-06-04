from __future__ import annotations

import sys

from .cli.entry import main
from .cli.utils import fatal

if __name__ == '__main__':
    try:
        exitcode = main()
    except KeyboardInterrupt:
        fatal('用户使用 Ctrl+C 或 SIGINT 终止了操作')
        sys.exit(130)
    else:
        sys.exit(exitcode)
