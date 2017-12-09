# -*- coding: utf-8 -*-
import json
import logging


DEFAULT_CONFIG_LOCATION = "/usr/local/etc/log_analyzer.conf"
DEFAULT_LOGGING_LEVEL = logging.DEBUG
DEFAULT_CONFIG = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "LOGGER_DIR": "./logger",
    "LOG_GLOB_TEMPLATE": "nginx-access-ui.log-*",
    "LOG_DATE_TEMPLATE": ["nginx-access-ui.log-%Y%m%d", "nginx-access-ui.log-%Y%m%d.gz"],
    "REPORT_DATE_TEMPLATE": "report-%Y.%m.%d.html",
    "TIMESTAMP_FILE": "/var/tmp/log_analyzer.ts",
    "SORT_FIELD": "time_sum",
    "MAX_PARSING_ERRORS": 100,
    "LOG_ENCODING": "utf-8",
    "REPORT_ENCODING": "utf-8"
}


def read_config(config_file=None):
    conf = DEFAULT_CONFIG
    if config_file:
        with open(config_file) as conf_file:
            conf.update(json.load(conf_file))
    return conf
