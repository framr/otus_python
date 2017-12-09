# -*- coding: utf-8 -*-
import os
import io
import json
from string import Template


TEMPLATE = "report.html"
_ROOT = os.path.abspath(os.path.dirname(__file__))


def _get_static_data_path(filename):
    return os.path.join(_ROOT, "static", filename)


def render_report(data, outfilename, sort_by, encoding="utf-8", template_file=None):
    """
    data: list of url time stats (dicts)
    """
    dump = json.dumps(sorted(data, key=lambda r: r[sort_by], reverse=True), encoding=encoding)
    template_filename = template_file or _get_static_data_path(TEMPLATE)
    with io.open(outfilename, "w", encoding=encoding) as outfile:
        with io.open(template_filename, encoding=encoding) as templ:
            outfile.write(Template(templ.read()).safe_substitute(table_json=dump))
