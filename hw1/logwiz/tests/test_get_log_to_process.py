import unittest
import os
from datetime import datetime

from logwiz.logutil import get_log_to_process


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures")
LOG_PATH = os.path.join(FIXTURE_PATH, "logs")


class GetLogToProcessTest(unittest.TestCase):
    def setUp(self):
        self.conf = {
                "LOG_GLOB_TEMPLATE": "nginx-access-ui.log-*",
                "LOG_DATE_TEMPLATE":  ["nginx-access-ui.log-%Y%m%d",
                                       "nginx-access-ui.log-%Y%m%d.gz"],
                "REPORT_GLOB_TEMPLATE": "report-*.html",
                "REPORT_DATE_TEMPLATE":  "report-%Y.%m.%d.html"
                }

    def test_no_logs_no_reports(self):
        self.conf["LOG_DIR"] = os.path.join(LOG_PATH, "log_no_logs")
        self.conf["REPORT_DIR"] = os.path.join(LOG_PATH, "report_no_logs")
        self.assertEquals(
                get_log_to_process(self.conf),
                (None, None)
                )

    def test_no_reports(self):
        self.conf["LOG_DIR"] = os.path.join(LOG_PATH, "log_last_20170701")
        self.conf["REPORT_DIR"] = os.path.join(LOG_PATH, "report_no_logs")
        self.assertEquals(
                get_log_to_process(self.conf),
                (os.path.join(self.conf["LOG_DIR"], "nginx-access-ui.log-20170701"),
                    datetime(2017, 07, 01))
                )

    def test_last_log_not_processed(self):
        self.conf["LOG_DIR"] = os.path.join(LOG_PATH, "log_last_20170701")
        self.conf["REPORT_DIR"] = os.path.join(LOG_PATH, "report_last_20170630")
        self.assertEquals(
                get_log_to_process(self.conf),
                (os.path.join(self.conf["LOG_DIR"], "nginx-access-ui.log-20170701"),
                    datetime(2017, 07, 01))
                )

    def test_last_log_processed(self):
        self.conf["LOG_DIR"] = os.path.join(LOG_PATH, "log_last_20170701")
        self.conf["REPORT_DIR"] = os.path.join(LOG_PATH, "report_last_20170701")
        self.assertEquals(
                get_log_to_process(self.conf),
                (None, None)
                )


if __name__ == "__main__":
    unittest.main()
