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
import io

from logwiz.logger import info, exception


_RE_PARTS = [
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
REGEXP = re.compile(r'\s+'.join(_RE_PARTS) + r'\s*\Z', flags=re.UNICODE)


def parse_line(line):
    match = REGEXP.match(line)
    return match.groupdict() if match else None


def _gen_parsed_lines(filename, encoding):
    if filename.endswith("gz"):
        with gzip.open(filename) as infile:
            for line in infile:
                yield parse_line(line.decode(encoding))
    else:
        with io.open(filename, encoding=encoding) as infile:
            for line in infile:
                yield parse_line(line)


def do_aggregate(filename, encoding="utf-8", max_errors=0):
    """
    apply custom aggregator class iteratively to log
    """
    parsed_records = _gen_parsed_lines(filename, encoding)
    stats = defaultdict(list)
    errors_count = 0
    for rec in parsed_records:
        try:
            url = rec['request'].split()[1]
            stats[url].append(float(rec['request_time']))
        except Exception:
            errors_count += 1
            exception("Error parsing record %s" % rec)
            if errors_count > max_errors:
                raise

    info("Got %d errors while parsing log" % errors_count)
    return stats


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


def parse_otus_log(filename, encoding="utf-8", top=None, max_errors=0):
    url_data = do_aggregate(filename, encoding=encoding, max_errors=max_errors)
    url_stats = calc_url_stats(url_data, top=top)
    return url_stats
