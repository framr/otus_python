import unittest

from logwiz.parser import OTUSRecordParser, OTUSStatAggregator


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
        self.assertEqual(res,
                {'url1': [1.0, 2.0, 3.0], 'url2': [0.1]})

    def test_norequest(self):
        r = {'request': 'GET url1 HTTP/1.1', 'request_time': '1.0'}
        self.assertRaises(KeyError, self.aggregator(r))


if __name__ == "__main__":
    unittest.main()
