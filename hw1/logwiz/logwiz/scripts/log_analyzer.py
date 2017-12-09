#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import time
import logging
from logging import info, exception
from argparse import ArgumentParser

from logwiz.conf import read_config, DEFAULT_CONFIG_LOCATION, DEFAULT_LOGGING_LEVEL
from logwiz.report import render_report
from logwiz.parser import parse_otus_log
from logwiz.logutil import get_log_to_process


def prepare_env(conf):
    info("Preparing environment")
    if not os.path.isdir(conf["REPORT_DIR"]):
        os.makedirs(conf["REPORT_DIR"])


def init_logger(level, log_dir=None):
    logfile = os.path.join(log_dir, "log-analyzer.log") if log_dir else None
    if log_dir and not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    logging.basicConfig(
            format='[%(asctime)s] %(levelname).1s %(message)s',
            datefmt="%Y.%m.%d %H:%M:%S",
            stream=sys.stdout if not logfile else None,
            filename=logfile,
            level=level
            )


def main():
    argparser = ArgumentParser()
    argparser.add_argument("--config", dest="config", type=str, default=DEFAULT_CONFIG_LOCATION,
                           help="config file")
    args = argparser.parse_args()
    conf = read_config(args.config)
    init_logger(log_dir=conf.get("LOGGER_DIR", None), level=DEFAULT_LOGGING_LEVEL)

    # XXX: We need a lock preventing from running two scripts simultaneously here
    try:
        prepare_env(conf)
    except OSError:
        exception("Error preparing environment")
        sys.exit(1)

    try:
        logfile = get_log_to_process(
                conf["LOG_DIR"],
                conf["LOG_GLOB_TEMPLATE"],
                conf["LOG_DATE_TEMPLATE"],
                conf["REPORT_DIR"],
                conf["REPORT_DATE_TEMPLATE"]
                )
    except Exception:
        exception("Unable to find logs to process")
        sys.exit(1)
    if not logfile:
        info("No logs to process")
        sys.exit(0)

    info("Processing logfile %s with date %s" % (logfile.name, logfile.date))
    try:
        url_stats = parse_otus_log(
                logfile.name,
                encoding="utf-8",
                top=conf["REPORT_SIZE"],
                max_errors=conf["MAX_PARSING_ERRORS"]
                )
    except Exception:
        exception("Error parsing and processing log")
        sys.exit(1)

    info("Rendering report for date %s" % logfile.date)
    try:
        outfile = os.path.join(
                conf["REPORT_DIR"],
                logfile.date.strftime(conf["REPORT_DATE_TEMPLATE"])
                )
        info("Report file: %s" % outfile)
        render_report(
                url_stats,
                outfile,
                conf["SORT_FIELD"],
                conf["REPORT_ENCODING"]
                )
    except Exception:
        exception("Error rendering report")
        try:
            os.remove(outfile)  # remove possibly malformed file
        except OSError:
            pass
        sys.exit(1)

    with open(conf["TIMESTAMP_FILE"], "w") as ts_file:
        timestamp = time.time()
        ts_file.write(str(timestamp))
        os.utime(conf["TIMESTAMP_FILE"], (timestamp, timestamp))


if __name__ == "__main__":
    main()
