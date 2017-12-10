# -*- coding: utf-8 -*-
import os
import unittest
from datetime import datetime

from logwiz.logutil import get_last_log


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures")
LOG_PATH = os.path.join(FIXTURE_PATH, "log_logutil")
LOG_PATH_FILES = [
        (os.path.join(LOG_PATH, "nginx-access-ui.log-20170630.gz"), datetime(2017, 06, 30)),
        (os.path.join(LOG_PATH, "nginx-access-ui.log-20170701"), datetime(2017, 07, 01))
        ]


class GetLastLogTest(unittest.TestCase):
    def test_last_log(self):
        log = get_last_log(LOG_PATH, r"nginx-access-ui.log-(?P<DATE>\d{8})(\.gz)?")

        etalon_name, etalon_date = max(LOG_PATH_FILES, key=lambda x: x[1])
        etalon_name = os.path.basename(etalon_name)
        self.assertEqual((log.name, log.date), (etalon_name, etalon_date))


if __name__ == "__main__":
    unittest.main()
