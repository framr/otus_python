# -*- coding: utf-8 -*-
# Utils for retrieving available logs. Normally such utils should be in separate package.

import re
import os
from collections import namedtuple
from datetime import datetime

LogWithDate = namedtuple("Log", "name date")


def get_last_log(log_dir, log_template):
    log_re = re.compile(log_template)
    if not os.path.exists(log_dir):
        return None

    last_log = last_log_date = None
    for fname in os.listdir(log_dir):
        m = log_re.match(fname)
        if not m:
            continue
        dt = m.group("DATE")
        if not last_log or dt > last_log_date:
            last_log, last_log_date = fname, dt
    return LogWithDate(last_log, datetime.strptime(last_log_date, "%Y%m%d")) if last_log else None
