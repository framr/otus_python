# -*- coding: utf-8 -*-
# Utils for retrieving available logs. Normally such utils should be in separate package.

import glob
import os
from datetime import datetime

from logwiz.logger import error, info


def extract_date(s, date_template):
    """
    Extract date from log name.
    date template: template recognized by datetime.strptime function.
    can be either string with template or a list of templates
    (date is taken from first successful match).
    output: datetime object
        in case of no match returns None
    """

    date = None
    if isinstance(date_template, list):
        for templ in date_template:
            try:
                date = datetime.strptime(s, templ)
            except ValueError:
                continue
            break
    else:
        try:
            date = datetime.strptime(s, date_template)
        except ValueError:
            pass
    return date


def get_logs_by_regexp_time(path, glob_template, datetime_template):
    """
    Generator yielding logs matching specific template in a path.
    glob_template: logs are filtered based on unix glob in this template.
    datetime_template: template used for extracting date from log name
    output: tuples with log name and log date (datetime object)
    """
    log_files = glob.glob(os.path.join(path, glob_template))
    for filename in log_files:
        log_date = extract_date(os.path.basename(filename), datetime_template)
        if not log_date:
            error("Malformed log name %s, date can not be extracted" % filename)

        yield filename, log_date


def get_last_log(path, glob_template, datetime_template):
    """
    Get last log in a path matching templates
    datetime_template: template used for extracting date from log name
    output: tuples with log name and log date (datetime object)
    """

    log_stream = get_logs_by_regexp_time(path, glob_template, datetime_template)
    last_log = None
    max_date = None
    for log, date in log_stream:
        if not max_date or date > max_date:
            last_log = log
            max_date = date

    return last_log, max_date


def get_log_to_process(conf):
    info("Searching for most recent log file")
    last_log, log_date = get_last_log(
        conf["LOG_DIR"],
        conf["LOG_GLOB_TEMPLATE"],
        conf["LOG_DATE_TEMPLATE"]
        )
    info("Found file %s for date %s" % (last_log, log_date))

    if not last_log:
        info("No valid logs found, abort")
        return None, None

    info("Searching for most recent report file")
    last_report, report_date = get_last_log(
            conf["REPORT_DIR"],
            conf["REPORT_GLOB_TEMPLATE"],
            conf["REPORT_DATE_TEMPLATE"]
            )
    info("Found report file %s for date %s" % (last_report, report_date))

    if last_report and report_date >= log_date:
        info("Last processed log %s is uptodate (cmp with %s)" % (last_report, last_log))
        return None, None

    return last_log, log_date
