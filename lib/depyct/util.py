# depyct/util.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
"""

"""
import array
import sys

py3k = sys.version_info >= (3, 0)
py27 = sys.version_info >= (2, 7) and not py3k
jython = sys.platform.startswith("java")
pypy = sys.platform.startswith("pypy")


class readonly_property(object):

    def __init__(self, fget):
        self.name = fget.__name__
        self.fget = fget

    def __get__(self, obj, typename=None):
        if obj is None:
            return self
        return self.fget(obj)

    def __set__(self, obj, value):
        raise TypeError("{} is a read-only value.".format(self.name))

    def __delete__(self, obj):
        raise TypeError("{} is a read-only value.".format(self.name))


def initialize_buffer(mode, size, color=None):
    if color is None:
        color = mode.transparent_color
    initial_value = color * size[0] * size[1]
    if py27:
        return bytearray(initial_value)
    else:
        return array.array("B", initial_value)
