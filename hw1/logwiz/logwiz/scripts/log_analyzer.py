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
from logwiz.logutil import get_last_log


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


def report_to_create(path, date, template):
    report_file = os.path.join(path, date.strftime(template))
    return report_file if not os.path.isfile(report_file) else None


def write_timestamp(fname):
    with open(fname, "w") as ts_file:
        timestamp = time.time()
        ts_file.write(str(timestamp))
        os.utime(fname, (timestamp, timestamp))


class NothingToProcess(Exception):
    pass


def main():
    argparser = ArgumentParser()
    argparser.add_argument("--config", dest="config", type=str, default=DEFAULT_CONFIG_LOCATION,
                           help="config file")
    args = argparser.parse_args()
    conf = read_config(args.config)
    init_logger(log_dir=conf.get("LOGGER_DIR", None), level=DEFAULT_LOGGING_LEVEL)

    try:
        prepare_env(conf)
    except BaseException:
        exception("Error preparing environment")
        sys.exit(1)

    try:
        last_log = get_last_log(conf["LOG_DIR"], conf["LOG_TEMPLATE"])
        if not last_log:
            info("No logs to process")
            raise NothingToProcess

        report_file = report_to_create(conf["REPORT_DIR"], last_log.date, conf["REPORT_DATE_TEMPLATE"])
        if not report_file:
            info("Last report for log %s is uptodate" % last_log.name)
            raise NothingToProcess
    except NothingToProcess:
        sys.exit(0)
    except BaseException:
        exception("Got error while searching for log to process")
        sys.exit(1)

    try:
        info("Processing logfile %s with date %s" % (last_log.name, last_log.date))
        url_stats = parse_otus_log(os.path.join(conf["LOG_DIR"], last_log.name), encoding=conf["LOG_ENCODING"],
                                   top=conf["REPORT_SIZE"], max_errors=conf["MAX_ERRORS"],
                                   max_errors_ratio=conf["MAX_ERRORS_RATIO"])
        info("Rendering report %s" % report_file)
        render_report(url_stats, report_file, conf["SORT_FIELD"], conf["REPORT_ENCODING"])
        write_timestamp(conf["TIMESTAMP_FILE"])
    except BaseException:
        exception("Error parsing and processing log")
        try:
            os.remove(report_file)  # remove possibly malformed file
        except OSError:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
