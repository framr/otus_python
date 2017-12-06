#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import time

from logwiz.logger import init_logger, info, exception
from logwiz.conf import read_config
from logwiz.report import render_report
from logwiz.parser import parse_otus_log
from logwiz.logutil import get_log_to_process


def prepare_env(conf):
    info("Preparing environment")
    if not os.path.isdir(conf["REPORT_DIR"]):
        os.makedirs(conf["REPORT_DIR"])


def main():

    conf = read_config()
    init_logger(path=conf.get("LOGGER_DIR", None))

    # XXX: We need a lock preventing from running two scripts simultaneously here

    try:
        prepare_env(conf)
    except OSError:
        exception("Error preparing environment")
        sys.exit(0)

    try:
        logfile, date = get_log_to_process(conf)
    except Exception:
        exception("Unable to find logs to process")
        sys.exit(0)

    if not logfile:
        info("No logs to process")
        sys.exit(0)

    info("Processing logfile %s with date %s" % (logfile, date))
    try:
        url_stats = parse_otus_log(logfile, top=conf["REPORT_SIZE"])
    except Exception:
        exception("Error parsing and processing log")
        sys.exit(0)

    info("Rendering report for date %s" % date)
    try:
        outfile = os.path.join(conf["REPORT_DIR"], date.strftime(conf["REPORT_DATE_TEMPLATE"]))
        info("Report file: %s" % outfile)
        render_report(url_stats, outfile, conf["SORT_FIELD"])

        with open(conf["TIMESTAMP_FILE"], "w") as ts_file:
            timestamp = time.time()
            ts_file.write(str(timestamp))
            os.utime(conf["TIMESTAMP_FILE"], (timestamp, timestamp))
    except Exception:
        exception("Error rendering report")
        sys.exit(0)


if __name__ == "__main__":
    main()
