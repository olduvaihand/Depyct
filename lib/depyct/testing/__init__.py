# depyct/testing/__init__.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
"""

"""
import os
import unittest


_DIR = os.path.dirname(os.path.abspath(__file__))


class DepyctUnitTest(unittest.TestCase):

    def read_data(self, path):
        with open(self.get_data_path(path), 'rb') as f:
            return f.read()

    def get_data_path(self, path):
        return os.path.join(
                _DIR, os.pardir, os.pardir, os.pardir, 'test', 'data', path)


def main():
    unittest.main()
