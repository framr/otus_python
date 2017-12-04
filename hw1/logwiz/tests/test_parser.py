import unittest
import os

from logwiz.parser import OTUSRecordParser, OTUSStatAggregator, do_aggregate,\
        calc_stats, calc_url_stats

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures")
LOG_PATH = os.path.join(FIXTURE_PATH, "do_aggregate")


class OTUSRecordParserTest(unittest.TestCase):

    def setUp(self):
        self.parser = OTUSRecordParser()

    def test_record_parser(self):
        record = '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390'
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

        res = self.parser(record)
        self.assertEquals(res, etalon)


class OTUSStatAggregatorTest(unittest.TestCase):
    def setUp(self):
        self.aggregator = OTUSStatAggregator()

    def test_aggregator(self):
        records = [
                {'request': 'GET url1 HTTP/1.1', 'request_time': '1.0'},
                {'request': 'GET url1 HTTP/1.1', 'request_time': '2.0'},
                {'request': 'GET url1 HTTP/1.1', 'request_time': '3.0'},
                {'request': 'GET url2 HTTP/1.1', 'request_time': '0.1'}
                ]

        for r in records:
            self.aggregator(r)

        res = self.aggregator.get_result()
        self.assertEqual(res, {'url1': [1.0, 2.0, 3.0], 'url2': [0.1]})

    def test_norequest(self):
        r = {'request': 'GET url1 HTTP/1.1', 'request_time': '1.0'}
        self.assertRaises(KeyError, self.aggregator(r))


class DoAggregateTest(unittest.TestCase):

    def setUp(self):
        self.parser = OTUSRecordParser()
        self.aggregator = OTUSStatAggregator()

    def test_do_aggregate1(self):
        log1 = os.path.join(LOG_PATH, "nginx-access-ui.log-20170701_2")
        self.aggregator.reset()
        do_aggregate(log1, self.parser, self.aggregator)
        res = self.aggregator.get_result()
        etalon = {
                '/api/v2/banner/25019354': [0.390],
                '/api/1/photogenic_banners/list/?server_name=WIN7RB4': [0.133]
                }
        self.assertEquals(res, etalon)

    def test_do_aggregate2(self):
        log1 = os.path.join(LOG_PATH, "nginx-access-ui.log-20170701_2_2")
        self.aggregator.reset()
        do_aggregate(log1, self.parser, self.aggregator)
        res = self.aggregator.get_result()
        etalon = {
                '/api/v2/banner/25019354': [0.390],
                '/api/1/photogenic_banners/list/?server_name=WIN7RB4': [0.133, 0.266]
                }
        self.assertEquals(res, etalon)


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
