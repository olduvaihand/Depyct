# depyct/image/pixel.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
"""
"""
from struct import Struct

from depyct import util


__all__ = [
    "Pixel",
    "component_property",
    "pixel_value_property",
    "struct_pixel_value_property",
    "pixel_maker"
]


class Pixel(object):
    """

    """

    def __init__(self, buffer):
        self.buffer = buffer

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
        for c in self.value:
            yield c

    def __getitem__(self, key):
        if isinstance(key, int):
            if key < 0:
                key += self.mode.components
            if key >= self.mode.components:
                raise IndexError("Component index is out of range.")
        return self.value[key]

    def __setitem__(self, key, value):
        if isinstance(key, int):
            if key < 0:
                key += self.mode.components
            if key >= self.mode.components:
                raise IndexError("Component index is out of range.")
        cur = list(self.value)
        cur[key] = value
        self.value = cur


class component_property(object):
    """

    """

    def __init__(self, index):
        self.index = index

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return obj[self.index]

    def __set__(self, obj, value):
        obj[self.index] = value

    def __delete__(self, obj):
        raise AttributeError("Can't delete a component.")


class pixel_value_property(object):
    """

    """

    def unpack(self, buffer):
        return tuple(buffer)

    def pack(self, *values):
        return values

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        if util.py27:
            s = b"".join(obj.buffer[:])
        else:
            s = obj.buffer[:]
        return self.unpack(s)

    def __set__(self, obj, value):
        value = tuple(value)
        if len(value) != obj.mode.components:
            raise ValueError
        obj.buffer[:] = self.pack(*value)

    def __delete__(self, obj):
        raise AttributeError("Can't delete a pixel value.")


class struct_pixel_value_property(pixel_value_property):
    """

    """

    def __init__(self, mode):
        bpc = mode.bits_per_component
        if mode._is_float:
            struct_type = {32: "f", 64: "d"}[bpc]
        else:
            struct_type = {8: "B", 16: "H", 32: "L", 64: "Q"}[bpc]
        self.pixel_struct = Struct("{}{}".format(mode.components, struct_type))

    def pack(self, *values):
        return self.pixel_struct.pack(*values)

    def unpack(self, buffer):
        return self.pixel_struct.unpack(buffer)


def pixel_maker(mode, value_property=None):
    """

    """
    if value_property is None:
        value_property = struct_pixel_value_property(mode)
    methods = {"value": value_property}
    for i, name in enumerate(mode.component_names):
        methods[name] = component_property(i)
    pixel_cls = type("{}Pixel".format(mode), (Pixel,), methods)
    pixel_cls.mode = mode
    return pixel_cls
