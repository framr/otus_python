# -*- coding: utf-8 -*-
# Utils for retrieving available logs. Normally such utils should be in separate package.

import glob
import os
from datetime import datetime

from logwiz.logger import info, error, exception


def extract_date(s, date_template):
    """
    Extract date from log name.
    date template: template recognized by datetime.strptime function. can be either string with template
    or a list of templates (date is taken from first successful match).
    output: datetime object
    """

    date = None
    if isinstance(date_template, list):
        for templ in date_template:
            try:
                date = datetime.strptime(s, templ)
            except:
                continue
            break
    else:
        date = datetime.strptime(s, date_template)
    return date


def get_logs_by_regexp(path, glob_template, datetime_template):
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
            exception("Malformed log name %s, date can not be extracted" % filename)

        yield filename, log_date


def get_last_log(path, glob_template, datetime_template):
    """
    Get last log in a path matching templates
    datetime_template: template used for extracting date from log name
    output: tuples with log name and log date (datetime object) 
    """

    log_stream = get_logs_by_regexp(path, glob_template, datetime_template)
    last_log = None
    max_date = None
    for log, date in log_stream:
        if not max_date or max_date > date:
            last_log = log
            max_date = date
 
    return last_log, max_date

