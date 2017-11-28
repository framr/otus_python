import re
import glob
import os
import sys


from logwiz.logger import info, error, exception


def logs_gen(path, glob_template, datetime_template, ignore_errors=False):
    log_files = glob.glob(os.path.join(path, glob_template))
    expr = re.compile(datetime_template)
    for filename in log_files:
        match = expr.match(filename)
        if not match:
            error("Malformed filename %s, date does not match" % filename)
            if not ignore_errors:
                sys.exit(0)
        
        log_date = match.group("DATE")
        yield filename, log_date


def get_last_log(path, glob_template, datetime_template, ignore_errors=False):

    log_stream = logs_gen(path, glob_template, datetime_template, ignore_errors=ignore_errors)

    last_log = None
    max_date = None
    for log, date in log_stream:
        if not max_date or max_date > log_date:
            last_log = filename
            max_date = log_date
 
    return last_log, max_date






