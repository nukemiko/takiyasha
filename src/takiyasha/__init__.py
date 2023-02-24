# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

from .loggingformatter import LoggingFormatter

__LOGGING_LEVEL = logging.DEBUG

consolehandler = logging.StreamHandler()
consolehandler.setLevel(__LOGGING_LEVEL)

consolehandler.setFormatter(LoggingFormatter())

logging.basicConfig(level=__LOGGING_LEVEL, handlers=[consolehandler])
logging.getLogger('root').name = __package__
