# depyct/image/pixel.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
"""
"""
import ctypes

from depyct import util

__all__ = ["Pixel", "pixel_maker"]

if util.py3k:
    long = int


class Pixel(ctypes.Structure):
    """

    """

    _pack_ = 1

    def __str__(self):
        return "<{}: {}>".format(self.__class__.__name__, tuple(self))

    if util.py27:
        def __unicode__(self):
            return unicode(str(self))

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, tuple(self))

    def __len__(self):
        return self.mode.components

    def __iter__(self):
        for c in self._fields_:
            yield getattr(self, c[0])

    @property
    def value(self):
        return tuple(self)

    @value.setter
    def value(self, value):
        try:
            value = tuple(value)
        except TypeError:
            value = (value,)
        if len(value) != self.mode.components:
            raise ValueError
        self[:] = value

    def __getitem__(self, key):
        if isinstance(key, (int, long)):
            if key < 0:
                key += self.mode.components
            if key >= self.mode.components:
                raise IndexError("Component index is out of range.")
            return getattr(self, self._fields_[key][0])
        return tuple(getattr(self, c[0]) for c in self._fields_[key])

    def __setitem__(self, key, value):
        if isinstance(key, (int, long)):
            if key < 0:
                key += self.mode.components
            if key >= self.mode.components:
                raise IndexError("Component index is out of range.")
            setattr(self, self._fields_[key][0], value)
        else:
            for i, c in enumerate(self._fields_[key]):
                setattr(self, c[0], value[i])


def pixel_maker(mode):
    """

    """

    bpc = mode.bits_per_component
    if mode._is_float:
        component_type = {#16: ctypes.c_uint16,
                          32: ctypes.c_float,
                          64: ctypes.c_double}[bpc]
    else:
        component_type = {8: ctypes.c_uint8,
                          16: ctypes.c_uint16,
                          32: ctypes.c_uint32,
                          64: ctypes.c_uint64}[bpc]

    attrs = {
            "_fields_": [(c, component_type) for c in mode.component_names],
            "mode": mode
        }
    pixel_cls = type("{}Pixel".format(mode), (Pixel,), attrs)
    return pixel_cls
