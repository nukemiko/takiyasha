from __future__ import annotations

from pathlib import Path

__VERSION__ = '0.7.0'

PROGNAME = Path(__file__).parent.name
DESCRIPTION = f'  将加密音乐文件的内容输出到指定的目录。\n' \
              f'  如果未指定输出目录，输出文件将会在当前工作目录下产生。\n' \
              f"  使用 '--formats' 选项查看支持的格式。"
EPILOG = f'{PROGNAME} 对输出数据的可用性（是否可以识别、播放等）不做任何保证。\n\n' \
         f'{PROGNAME} 默认会为输出文件搜索并补全标签信息和封面数据，这一过程需要网络。\n' \
         f"如果您的网络环境不好，可以添加选项 '--avoid-search-tag' 以改变这一默认行为。\n\n" \
         f'项目地址：https://github.com/nukemiko/takiyasha'
