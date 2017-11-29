# -*- coding: utf-8 -*-
# Here be dragons
# (generic utils for parsing logs + OTUS log parser)
# OTUS log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';


from logwiz.logger import info, error, exception


class RecordParser(object):
    """
    class parsing single log line
    """
    def __init__(self):
        pass
    def __call__(self, rec):
        pass

class StatAggregator(object):
    """
    class aggregating statistics from log lines
    """
    def __init__(self):
        self._result = None
    def __call__(self, recs):
        raise NotImplementedError
    def get_result(self):
        return self._result

class OTUSStatAggregator(StatAggregator):
    def __init__(self):
        self._result = {}
    def __call__(self, recs):
        pass


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
    for line in gen_lines
        yield rec_parser(gen_lines)

def do_aggregate(filename, rec_parser, aggregator):
    """
    apply custom aggregator class iteratively to log
    """ 
    log = _gen_open(filename)
    log_lines = _gen_lines_from_streams(log)
    parsed_records = _gen_parser(log_lines)
    for rec in parsed_records:
        aggregator(rec) 


def parse_otus_log(filename):
    parser = RecordParser()
    aggregator = OTUSStatAggregator()
    do_aggregate(filename, parser, aggregator) 
    return aggregator.get_value()



