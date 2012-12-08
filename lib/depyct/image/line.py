# depyct/image/line.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
"""
"""
import ctypes

from depyct import util

__all__ = ["Line"]


if util.py3k:
    long = int


class Line(ctypes.Structure):
    """

    """

    _pack_ = 1

    def __str__(self):
        return "<{}: {}>".format(self.__class__.__name__,
                                 tuple(p.value for p in self))

    if util.py27:
        def __unicode__(self):
            return unicode(str(self))

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__,
                               tuple(p.value for p in self))

    def __len__(self):
        return len(self.pixels)

    def __getitem__(self, key):
        if isinstance(key, (int, long)):
            return self.pixels[key]
        elif isinstance(key, slice):
            p_start, p_stop, p_step = key.indices(len(self))
            width = len(range(p_start, p_stop, p_step))
            res = self.image_cls(self.mode, size=(width, 1))
            for i, pixel in enumerate(self.pixels[key]):
                res[i, 0].value = pixel.value
            return res
        raise TypeError("Image indices must be int, slice, or a "
                        "two-tuple composed of ints, slices, or both. {}".format(type(key)))

    def __setitem__(self, key, value):
        if isinstance(key, (int, long)):
            if key < 0:
                key += len(self)
            if key >= len(self):
                raise IndexError("Pixel index is out of range.")
            self[key].value = value
        elif isinstance(key, slice):
            p_start, p_stop, p_step = key.indices(len(self))
            offsets = len(range(p_start, p_stop, p_step))
            assert len(value) == offsets
            for p, v in zip(self.pixels[key], value):
                p.value = v
        else:
            raise TypeError("Image indices must be int, slice, or a "
                            "two-tuple composed of ints, slices, or both.")

    def __iter__(self):
        for p in self.pixels:
            yield p
