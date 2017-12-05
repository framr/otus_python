# -*- coding: utf-8 -*-
# Here be dragons
# (generic utils for parsing logs + OTUS log parser)
# OTUS log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
import re
import gzip
from collections import defaultdict

from logwiz.logger import error, info


class RecordParser(object):
    """
    Class parsing single log line
    """
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, rec):
        raise NotImplementedError


class StatAggregator(object):
    """
    Class aggregating statistics from log lines.
    """
    def __init__(self, *args, **kwargs):
        self._result = None

    def __call__(self, recs):
        raise NotImplementedError

    def get_result(self):
        return self._result

    def reset(self):
        return NotImplementedError


class OTUSRecordParser(RecordParser):
    def __init__(self, *args, **kwargs):
        _re_parts = [
            r'(?P<remote_addr>\S+)',
            r'(?P<remote_user>\S+)',
            r'(?P<http_x_real_ip>\S+)',
            r'\[(?P<time_local>.+)\]',
            r'"(?P<request>.+)"',
            r'(?P<status>\d+)',
            r'(?P<body_bytes_sent>\S+)',
            r'"(?P<http_referer>.+)"',
            r'"(?P<http_user_agent>.+)"',
            r'"(?P<http_x_forwarded_for>.+)"',
            r'"(?P<http_X_REQUEST_ID>.+)"',
            r'"(?P<http_X_RB_USER>.+)"',
            r'(?P<request_time>\S+)',
            ]
        _regexp = r'\s+'.join(_re_parts) + r'\s*\Z'
        self._regexp = re.compile(_regexp)

    def __call__(self, rec):
        match = self._regexp.match(rec)
        return match.groupdict()


class OTUSStatAggregator(StatAggregator):
    def __init__(self, *args, **kwargs):
        super(OTUSStatAggregator, self).__init__(*args, **kwargs)
        self._result = defaultdict(list)
        self._ignore_request_errors = kwargs.get("ignore_request_errors", False)
        self._error_count = 0

    def __call__(self, rec):
        request = rec['request']

        try:
            url = request.split()[1]
        except IndexError:
            error("Error parsing record %s" % rec)
            if not self._ignore_request_errors:
                raise
            else:
                self._error_count += 1
                return

        request_time = float(rec['request_time'])
        self._result[url].append(request_time)

    def cnt_errors(self):
        return self._error_count

    def reset(self):
        self._result = defaultdict(list)
        self._error_count = 0


def _gen_open(filename):
    if filename.endswith("gz"):
        with gzip.open(filename) as infile:
            yield infile
    else:
        with open(filename) as infile:
            yield infile


def _gen_lines_from_streams(gen_stream):
    for s in gen_stream:
        for line in s:
            yield line


def _gen_parsed(gen_lines, rec_parser):
    """
    gen_lines: generator yielding log lines
    rec_parser: line parser
    output: generator of parsed records
    """
    for line in gen_lines:
        yield rec_parser(line)


def do_aggregate(filename, rec_parser, aggregator):
    """
    apply custom aggregator class iteratively to log
    """
    log = _gen_open(filename)
    log_lines = _gen_lines_from_streams(log)
    parsed_records = _gen_parsed(log_lines, rec_parser)
    for rec in parsed_records:
        aggregator(rec)


def calc_stats(data):
    """
    data: array of floats
    output: basic statistics - sum, avg, median, max, count
    """
    if not data:
        return {}

    _count = len(data)
    _sum = sum(data)
    _avg = _sum / _count
    _sorted = sorted(data)
    _med = _sorted[_count / 2]
    _max = _sorted[-1]
    return {
            "count": _count,
            "sum": _sum,
            "avg": _avg,
            "med": _med,
            "max": _max
            }


def calc_url_stats(url_data, top=None):
    """
    url_data: dict url -> time stats
    output: list of dicts with url name and time stats.
    only top urls by avg time are returned.
    """
    url_stats = {}
    total_time = 0
    total_count = 0
    for url, data in url_data.iteritems():
        url_stats[url] = calc_stats(data)
        total_time += url_stats[url]["sum"]
        total_count += url_stats[url]["count"]

    result = []
    for url in sorted(url_stats, key=lambda url: url_stats[url]['avg'], reverse=True)[:top]:
        result.append({
            "url": url,
            "count": url_stats[url]["count"],
            "time_avg": round(url_stats[url]["avg"], 3),
            "time_sum": round(url_stats[url]["sum"], 3),
            "time_max": round(url_stats[url]["max"], 3),
            "time_med": round(url_stats[url]["med"], 3),
            "count_perc": round(100 * float(url_stats[url]["count"]) / total_count, 3),
            "time_perc": round(100 * float(url_stats[url]["sum"]) / total_time, 3)
            })
    return result


def parse_otus_log(filename, top=None):
    parser = OTUSRecordParser()
    aggregator = OTUSStatAggregator(ignore_request_errors=True)
    do_aggregate(filename, parser, aggregator)
    info("got %d errors while parsing log" % aggregator.cnt_errors())

    url_data = aggregator.get_result()
    url_stats = calc_url_stats(url_data, top=top)
    return url_stats
