# -*- coding: utf-8 -*-
import os
import json


TEMPLATE = "report.html"
_ROOT = os.path.abspath(os.path.dirname(__file__))


def _get_static_data_path(filename):
    return os.path.join(_ROOT, "static", filename)


def _render(template_filename, out_filename, data):
    with open(out_filename, "w") as outfile:
        with open(template_filename) as templ:
            for line in templ:
                if "$table_json" in line:
                    outfile.write(line.replace("$table_json", data))
                else:
                    outfile.write(line)


def render_report(data, outfilename, sort_by="count"):
    """
    data: list of url time stats (dicts)
    """
    dump = json.dumps(sorted(data, key=lambda r: r[sort_by], reverse=True))
    template = _get_static_data_path(TEMPLATE),
    _render(template, outfilename, dump)
