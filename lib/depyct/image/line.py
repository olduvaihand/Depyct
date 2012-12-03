# depyct/image/line.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
"""
"""
from depyct import util

__all__ = ["Line"]


Image = None


class Line(object):
    """

    """

    def __init__(self, mode, buffer):
        self.mode = mode
        self.buffer = buffer
        self._length = len(self.buffer) // self.mode.bytes_per_pixel

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
        return self._length

    def __getitem__(self, key):
        if isinstance(key, int):
            if key < 0:
                key += len(self)
            if key >= len(self):
                raise IndexError("Pixel index is out of range.")
            start = key * self.mode.bytes_per_pixel
            end = start + self.mode.bytes_per_pixel
            return self.mode.pixel_cls(self.buffer[start:end])
        elif isinstance(key, slice):
            p_start, p_stop, p_step = key.indices(len(self))
            width = len(range(p_start, p_stop, p_step))
            res = Image(self.mode, size=(width, 1))
            for i, pixel in enumerate(range(p_start, p_stop, p_step)):
                res[i, 0].value = self[pixel].value
            return res
        raise TypeError("Image indices must be int, slice, or a "
                        "two-tuple composed of ints, slices, or both.")

    def __setitem__(self, key, value):
        if isinstance(key, int):
            if key < 0:
                key += len(self)
            if key >= len(self):
                raise IndexError("Pixel index is out of range.")
            self[key].value = value
        elif isinstance(key, slice):
            p_start, p_stop, p_step = key.indices(len(self))
            offsets = len(range(p_start, p_stop, p_step))
            assert len(value) == offsets
            for i, pixel in zip(range(p_start, p_stop, p_step), value):
                self[i].value = pixel
        else:
            raise TypeError("Image indices must be int, slice, or a "
                            "two-tuple composed of ints, slices, or both.")

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]


def register_image_cls(image_cls):
    global Image
    Image = image_cls
