#!/usr/bin/env python
import unittest


class SomeTest(unittest.TestCase):

    def test(self):
        self.failUnless(True)


if __name__ == "__main__":
    unittest.main()
