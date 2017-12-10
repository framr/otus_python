# -*- coding: utf-8 -*-
import unittest
import os

from logwiz.parser import do_aggregate, parse_line, calc_stats, calc_url_stats, ParseError

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures")
LOG_PATH = os.path.join(FIXTURE_PATH, "do_aggregate")


class ParseLineTest(unittest.TestCase):
    def test_parse_line(self):
        record = u'1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390'
        etalon = {
                    'remote_addr': '1.196.116.32',
                    'remote_user': '-',
                    'http_x_real_ip': '-',
                    'time_local': '29/Jun/2017:03:50:22 +0300',
                    'request': 'GET /api/v2/banner/25019354 HTTP/1.1',
                    'status': '200',
                    'body_bytes_sent': '927',
                    'http_referer': '-',
                    'http_user_agent': 'Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5',
                    'http_x_forwarded_for': '-',
                    'http_X_REQUEST_ID': '1498697422-2190034393-4708-9752759',
                    'http_X_RB_USER': 'dc7161be3',
                    'request_time': '0.390'
                }

        res = parse_line(record)
        self.assertEquals(res, etalon)


class DoAggregateTest(unittest.TestCase):
    def test_do_aggregate1(self):
        log1 = os.path.join(LOG_PATH, "nginx-access-ui.log-20170701_2")
        res = do_aggregate(log1)
        etalon = {
                '/api/v2/banner/25019354': [0.390],
                '/api/1/photogenic_banners/list/?server_name=WIN7RB4': [0.133]
                }
        self.assertEquals(res, etalon)

    def test_do_aggregate2(self):
        log1 = os.path.join(LOG_PATH, "nginx-access-ui.log-20170701_2_2")
        res = do_aggregate(log1)
        etalon = {
                '/api/v2/banner/25019354': [0.390],
                '/api/1/photogenic_banners/list/?server_name=WIN7RB4': [0.133, 0.266]
                }
        self.assertEquals(res, etalon)

    def test_do_aggregate_parse_errors_count_above_thresh(self):
        log1 = os.path.join(LOG_PATH, "nginx-access-ui.log-20170701_2_3")
        self.assertRaises(TypeError, do_aggregate, log1, max_errors=1)

    def test_do_aggregate_parse_errors_count_below_thresh(self):
        log1 = os.path.join(LOG_PATH, "nginx-access-ui.log-20170701_2_3")
        try:
            do_aggregate(log1, max_errors=2)
        except Exception:
            self.fail("Exceptions should be suppressed here")

    def test_do_aggregate_parse_errors_ratio_above_thresh(self):
        log1 = os.path.join(LOG_PATH, "nginx-access-ui.log-20170701_2_3")
        self.assertRaises(ParseError, do_aggregate, log1, max_errors_ratio=50.0)

    def test_do_aggregate_parse_errors_ratio_below_thresh(self):
        log1 = os.path.join(LOG_PATH, "nginx-access-ui.log-20170701_2_3")
        try:
            do_aggregate(log1, max_errors_ratio=70.0)
        except ParseError:
            self.fail("Exceptions should be suppressed by max_errors_ratio")


class CalcStatsTest(unittest.TestCase):

    def test_calc_stats_empty(self):
        res = calc_stats([])
        self.assertEquals(res, {})

    def test_calc_stats1(self):
        res = calc_stats([0.0])
        self.assertEquals(
            res,
            {
                "count": 1,
                "sum": 0.0,
                "avg": 0.0,
                "med": 0.0,
                "max": 0.0,
            }
            )

    def test_calc_stats2(self):
        res = calc_stats([0.0, 1.0])
        self.assertEquals(
            res,
            {
                "count": 2,
                "sum": 1.0,
                "avg": 0.5,
                "med": 1.0,
                "max": 1.0,
            }
            )

    def test_calc_stats3(self):
        res = calc_stats([0.0, 1.0, 2.0])
        self.assertEquals(
            res,
            {
                "count": 3,
                "sum": 3.0,
                "avg": 1.0,
                "med": 1.0,
                "max": 2.0
                })


class CalcUrlStatsTest(unittest.TestCase):

    def test_calc_url_stats(self):
        data = {
            "url1": [2.0],
            "url2": [2.0, 2.0, 2.0]
            }

        self.assertEquals(
                calc_url_stats(data), [
                    {
                        "url": "url1",
                        "count": 1,
                        "time_avg": 2.0,
                        "time_sum": 2.0,
                        "time_max": 2.0,
                        "time_med": 2.0,
                        "count_perc": 25.0,
                        "time_perc": 25.0
                        },
                    {
                        "url": "url2",
                        "count": 3,
                        "time_avg": 2.0,
                        "time_sum": 6.0,
                        "time_max": 2.0,
                        "time_med": 2.0,
                        "count_perc": 75.0,
                        "time_perc": 75.0
                        }
                    ]
                )


if __name__ == "__main__":
    unittest.main()
