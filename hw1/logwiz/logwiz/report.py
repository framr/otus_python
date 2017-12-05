# -*- coding: utf-8 -*-
import os
import json

from logwiz.logger import info, exception


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


def render_report(data, outfilename, sort_by):
    """
    data: list of url time stats (dicts)
    """
    dump = json.dumps(sorted(data, key=lambda r: r[sort_by], reverse=True))
    template = _get_static_data_path(TEMPLATE)
    info("Using template file %s" % template)

    try:
        _render(template, outfilename, dump)
    except Exception:
        exception("Error rendering template")
        try:
            os.remove(template) # remove possibly malformed file
        except Exception:
            pass
