from __future__ import annotations

from pathlib import Path

PROGNAME = Path(__file__).parent.name
DESCRIPTION = f'  {PROGNAME} - Python 版本的音乐解密工具'
EPILOG = f'{PROGNAME} 对输出数据的可用性（是否可以识别、播放等）不做任何保证。\n\n' \
         f'{PROGNAME} 的默认行为（为输出文件补全标签）需要联网，\n' \
         f'如果您的网络环境不好，请查看帮助，并添加适当的选项以改变这一默认行为。\n\n' \
         f'项目地址：https://github.com/nukemiko/takiyasha/tree/remaked'
