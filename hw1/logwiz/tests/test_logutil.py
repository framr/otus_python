#!/usr/bin/env python

import os
import unittest
from datetime import datetime

from logwiz.logutil import extract_date, get_logs_by_regexp_time, get_last_log


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures")
LOG_PATH = os.path.join(FIXTURE_PATH, "log_logutil")
LOG_PATH_FILES = [
        (os.path.join(LOG_PATH, "nginx-access-ui.log-20170630.gz"), datetime(2017, 06, 30)),
        (os.path.join(LOG_PATH, "nginx-access-ui.log-20170701"), datetime(2017, 07, 01))
        ]


class ExtractDateTest(unittest.TestCase):

    def test_simple_template_match(self):
        self.assertEqual(
                extract_date("report-2017.10.11.html", "report-%Y.%m.%d.html"),
                datetime(2017, 10, 11)
                )

    def test_simple_template_nomatch(self):
        self.assertIsNone(
                extract_date("report-2017.10-11.html", "report-%Y.%m.%d.html"))

    def test_simple_template_notequal(self):
        self.assertNotEqual(
                extract_date("report-2017.10.11.html", "report-%Y.%m.%d.html"),
                datetime(2017, 10, 12)
                )

    def test_list_template_match1(self):
        self.assertEqual(
                extract_date("report-2017.10.11.html",
                             ["report-%Y.%m.%d.html", "report-%Y.%m.%d.html.gz"]),
                datetime(2017, 10, 11)
                )

    def test_list_template_match2(self):
        self.assertEqual(
                extract_date("report-2017.10.11.html.gz",
                             ["report-%Y.%m.%d.html", "report-%Y.%m.%d.html.gz"]),
                datetime(2017, 10, 11)
                )

    def test_list_template_nomatch(self):
        self.assertIsNone(
                extract_date("report-2017.10.11.html.gz",
                             ["report-%Y.%m.%d.htmlxxx", "report-%Y.%m.%d.htmlyyy"])
                )

    def test_list_template_notequal(self):
        self.assertNotEqual(
                extract_date("report-2017.10.11.html",
                             ["report-%Y.%m.%d.html", "report-%Y.%m.%d.html.gz"]),
                datetime(2011, 10, 11)
                )


class GetLogsByRegexpTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_logs_list(self):
        logs = get_logs_by_regexp_time(
                LOG_PATH,
                "nginx-access-ui.log-*",
                ["nginx-access-ui.log-%Y%m%d.gz",  "nginx-access-ui.log-%Y%m%d"])
        self.assertEqual(
            set(logs),
            set(LOG_PATH_FILES)
        )

    def test_no_match(self):
        logs = get_logs_by_regexp_time(
                LOG_PATH,
                "apache-access-ui.log-*",
                ["nginx-access-ui.log-%Y%m%d.gz",  "nginx-access-ui.log-%Y%m%d"])
        self.assertEqual(len(list(logs)), 0)

    def test_logs_list_bad_datetime(self):
        logs = list(get_logs_by_regexp_time(
                LOG_PATH,
                "nginx-access-ui.log-*",
                ["nginx-access-ui.log-%Y.%m.%d.gz",  "nginx-access-ui.log-%Y.%m.%d"]))
        self.assertEqual(
            set(log_data[0] for log_data in logs),
            set(d[0] for d in LOG_PATH_FILES)
        )
        self.assertEqual(
            list(log_data[1] for log_data in logs),
            [None, None]
        )


class GetLastLogTest(unittest.TestCase):

    def test_last_log(self):
        name, date = get_last_log(
                LOG_PATH,
                "nginx-access-ui.log-*",
                ["nginx-access-ui.log-%Y%m%d.gz",  "nginx-access-ui.log-%Y%m%d"])

        etalon_name, etalon_date = max(LOG_PATH_FILES, key=lambda x: x[1])
        self.assertEqual(
            (name, date), (etalon_name, etalon_date))


if __name__ == "__main__":
    unittest.main()
