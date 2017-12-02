# -*- coding: utf-8 -*-
"""
XXX: this should be a part of separate package
"""

import sys
import os
import logging
from logging import info, error, exception


DEFAULT_LOGGING_LEVEL = logging.DEBUG

logging.basicConfig(
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt="%Y.%m.%d %H:%M:%S",
        stream=sys.stdout,
        level=DEFAULT_LOGGING_LEVEL
)


def init_logger(path=None, prepare_env=True):

    stream = sys.stdout
    logfile = None
    if path:
        stream = None
        logfile = os.path.join(path, "log-analyzer.log")

        if not os.path.isdir(path) and prepare_env:
            info("Creating log dir %s" % path)
            os.makedirs(path)

    logging.basicConfig(
            format='[%(asctime)s] %(levelname).1s %(message)s',
            datefmt="%Y.%m.%d %H:%M:%S",
            stream=stream,
            filename=logfile,
            level=DEFAULT_LOGGING_LEVEL
    )
