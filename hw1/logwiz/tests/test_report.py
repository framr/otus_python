# -*- coding: utf-8 -*-
import unittest
import os
from tempfile import NamedTemporaryFile
from textwrap import dedent

from logwiz.report import render_report


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures")
TEMPLATE_PATH = os.path.join(FIXTURE_PATH, "report")


class RenderTest(unittest.TestCase):
    def test_render(self):
        data = [{"url": "url1", "time": 1.0}, {"url": "url2", "time": 2.0}]
        test_template = dedent(
            """
            xxx
            yyy
            !function($) {
                var table = $table_json;
                var reportDates;
                zzz
                fff
                fff
            """
            )
        template_file = NamedTemporaryFile(mode='wb', dir=TEMPLATE_PATH, delete=False)
        template_file.write(test_template)
        template_file.close()
        output_file = NamedTemporaryFile(mode='wb', dir=TEMPLATE_PATH, delete=False)
        output_file.close()

        render_report(data, output_file.name, sort_by='time', template_file=template_file.name)
        with open(output_file.name) as temp:
            result = temp.read()

        etalon = dedent(
                """
                xxx
                yyy
                !function($) {
                    var table = [{"url": "url2", "time": 2.0}, {"url": "url1", "time": 1.0}];
                    var reportDates;
                    zzz
                    fff
                    fff
                """)

        self.assertEquals(
                etalon,
                result
                )
        os.remove(template_file.name)
        os.remove(output_file.name)


if __name__ == "__main__":
    unittest.main()
