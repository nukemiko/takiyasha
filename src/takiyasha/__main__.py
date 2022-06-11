from __future__ import annotations

import sys

from .entry import entry
from .utils import fatal


def main():
    try:
        exitcode = entry()
    except KeyboardInterrupt:
        fatal('用户使用 Ctrl+C 或 SIGINT 终止了操作')
        sys.exit(130)
    else:
        sys.exit(exitcode)


if __name__ == '__main__':
    main()
