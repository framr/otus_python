from argparse import ArgumentParser
import json
import sys
import os

from logwiz.logger import error, info


DEFAULT_CONFIG_LOCATION = "/usr/local/etc/log_analyzer.conf"
DEFAULT_CONFIG = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "LOGGER_DIR": "./logger",
    "LOG_GLOB_TEMPLATE": "nginx-access-ui.log-*",
    "LOG_DATE_TEMPLATE": ["nginx-access-ui.log-%Y%m%d", "nginx-access-ui.log-%Y%m%d.gz"],
    "REPORT_GLOB_TEMPLATE": "report-*.html",
    "REPORT_DATE_TEMPLATE": "report-%Y.%m.%d.html",
    "TIMESTAMP_FILE": "/var/tmp/log_analyzer.ts"
}


def read_config():
    argparser = ArgumentParser()
    argparser.add_argument("--config", dest="conf", type=str, default=None,
            help="config file")
    args = argparser.parse_args()

    conf = DEFAULT_CONFIG
    if args.conf:
        if not os.path.isfile(args.conf):
            error("Provided config file %s is not a valid file, abort")
            sys.exit(0)
        info("Reading config from custom conf file %s" % args.conf)
        conf = json.load(args.conf)

    elif os.path.isfile(DEFAULT_CONFIG_LOCATION):
        info("Found external config file %s, reading config from it" % DEFAULT_CONFIG_LOCATION)
        conf = json.load(DEFAULT_CONFIG_LOCATION)
    else:
        info("No config files found, using defaults")

    return conf
