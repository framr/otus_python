#import re
import glob
import os
#import sys
from datetime import datetime

from logwiz.logger import info, error, exception


def extract_date(s, date_template):
    
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


def logs_gen(path, glob_template, datetime_template):
    log_files = glob.glob(os.path.join(path, glob_template))
    for filename in log_files:
        log_date = extract_date(os.path.basename(filename), datetime_template)
        if not log_date:
            exception("Malformed log name %s, date can not be extracted" % filename)

        yield filename, log_date


def get_last_log(path, glob_template, datetime_template):

    log_stream = logs_gen(path, glob_template, datetime_template)
    last_log = None
    max_date = None
    for log, date in log_stream:
        if not max_date or max_date > date:
            last_log = log
            max_date = date
 
    return last_log, max_date






