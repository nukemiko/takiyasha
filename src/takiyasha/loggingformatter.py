# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

import colorama as clr

clr.init()


class LoggingFormatter(logging.Formatter):
    DEFAULT_FORMAT = f'{clr.Style.RESET_ALL}<{clr.Fore.CYAN}%(name)s{clr.Style.RESET_ALL}> ' \
                     f'{{lvlnamecolor}}%(levelname)s{clr.Style.RESET_ALL}{{post_lvlname_blank}}: ' \
                     f'{{msgcolor}}%(message)s{clr.Style.RESET_ALL}'
    COLOR_CASE_BY_LEVELNO = {
        logging.DEBUG   : {
            'lvlnamecolor'      : clr.Style.DIM + clr.Fore.WHITE,
            'msgcolor'          : clr.Fore.WHITE,
            'post_lvlname_blank': ' ' * 3
        },
        logging.INFO    : {
            'lvlnamecolor'      : clr.Style.BRIGHT + clr.Fore.WHITE,
            'msgcolor'          : clr.Fore.WHITE,
            'post_lvlname_blank': ' ' * 4
        },
        logging.WARNING : {
            'lvlnamecolor'      : clr.Style.BRIGHT + clr.Fore.YELLOW,
            'msgcolor'          : clr.Fore.YELLOW,
            'post_lvlname_blank': ' ' * 1
        },
        logging.ERROR   : {
            'lvlnamecolor'      : clr.Style.BRIGHT + clr.Fore.RED,
            'msgcolor'          : clr.Fore.RED,
            'post_lvlname_blank': ' ' * 3
        },
        logging.CRITICAL: {
            'lvlnamecolor'      : clr.Back.RED + clr.Fore.WHITE,
            'msgcolor'          : clr.Back.RED + clr.Fore.WHITE,
            'post_lvlname_blank': ' ' * 0
        }
    }

    def format(self, record: logging.LogRecord) -> str:
        color_case = self.COLOR_CASE_BY_LEVELNO.get(record.levelno, logging.INFO)
        formatter = logging.Formatter(self.DEFAULT_FORMAT.format_map(color_case))

        return formatter.format(record)
