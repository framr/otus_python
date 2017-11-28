#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Here be dragons

import sys

from logwiz.logger import init_logger, info, error, exception
from logwiz.conf import read_config
from logwiz.report import render_report
from logwiz.parser import parse_log
from logwiz.logutil import get_last_log


def get_log_to_process(conf):

    info("Searching for most recent log file")    
    logfile, log_date = get_last_log(
        conf["LOG_DIR"],
        conf["LOG_GLOB_TEMPLATE"],
        conf["LOG_DATE_TEMPLATE"],
        ignore_errors=True
        )
    info("Found file %s" % logfile)

    if not logfile:
        info("No valid logs found, abort")
        sys.exit(0)

    info("Searching for most recent report file")     
    last_report, report_date = get_last_log(
            conf["REPORT_DIR"],
            conf["REPORT_GLOB_TEMPLATE"],
            conf["REPORT_DATE_TEMPLATE"],
            ignore_errors=True
    )
    info("Found report file %s" % last_processed_log)

    if last_report and report_date >= logfile_date:
        info("Last processed log %s is uptodate (cmp with %s)" % (last_processed_log, logfile))
        sys.exit(0)

    return logfile, log_date


def main():

    conf = read_config()
    init_logger(path=conf.get("LOGGER_DIR", None))

    try:
        logfile, date = get_log_to_process(conf)
    except:
        exception("Unable to get log to process")
        sys.exit(0) 
    

    info("Processing logfile %s with date %s" % (logfile, date))
    try:
        parsed_data = parse_log(logfile)
    except:
        exception("Error parsing log")
        sys.exit(0)    

    info("Rendering report") 
    try:
        report = render_report(parsed_data, outfile)
    except:
        exception("Error rendering report")
        sys.exit(0)


if __name__ == "__main__":
    main()


