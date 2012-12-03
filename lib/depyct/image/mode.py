# depyct/image/mode.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
"""

"""
import operator


class ImageMode(str):
    """The :class:`Mode` objects offer a number of attributes and methods
    that can be used for implementing generic algorithms that work on 
    different types of images.

    :attr:`.components`
        The number of components per pixel (e.g. 4 for an RGBA image).

    :attr:`.component_names`
        A :class:`tuple` of strings containing the names of each component.

    :attr:`.bits_per_component`
        8, 16, 32, or 64.

    :attr:`.bytes_per_pixel`
        ``components * bits_per_component // 8``, only available for non planar
        modes.

    :attr:`.planar`
        :class:`bool`, ``True`` if the image components reside in a separate
        plane.

    :attr:`.subsampling`
        A tuple that for each component contains a tuple of two integers that
        represent the amount of downsampling in the horizontal and vertical
        direction, respectively.

    :attr:`.x_divisor`
        ``max(x for x, y in subsampling)``; the width of an image that uses
        this mode must be divisible by this value.

    :attr:`.y_divisor`
        ``max(y for x, y in subsampling)``; the height of an image that uses
        this mode must be divisible by this value.

    :attr:`.intervals`
        A tuple that for each component in the mode contains a tuple of two
        integers or floats: the minimum and maximum valid value for the
        component.

    :attr:`.transparent_color`
        A tuple of component values representing a transparent color in a
        particular mode.

    """

    def __new__(cls, *args, **kwargs):
        return str.__new__(cls, "")

    def __init__(self, component_names, bits_per_component=8, planar=False,
            subsampling=None, intervals=None, transparent_color=None):
        super(ImageMode, self).__init__()
        self.components = len(component_names)
        self.component_names = tuple(component_names)
        self.bits_per_component = bits_per_component
        self.planar = planar
        self.subsampling = subsampling or ((1, 1),)*self.components
        self.intervals = intervals or \
                         ((0, 2**self.bits_per_component - 1),)*self.components
        self.x_divisor = max(x for x, y in self.subsampling)
        self.y_divisor = max(y for x, y in self.subsampling)
        self.transparent_color = transparent_color or \
                                 tuple(i[0] for i in self.intervals)

    def _create_pixel_cls(self):
        from .pixel import pixel_maker
        # update this to deal with half-floats
        self.pixel_cls = pixel_maker(self)

    @property
    def _is_float(self):
        return self.endswith("F") or isinstance(self.intervals[0][0], float)

    def __repr__(self):
        res = "<ImageMode {}: {}".format(self, ", ".join(self.component_names))
        if self.bits_per_component != 8:
            res += "; bits_per_component={}".format(self.bits_per_component)
        if self.planar:
            res += "; planar=True"
        if self.subsampling != ((1, 1),)*self.components:
            res += "; subsampling={}".format(self.subsampling)
        if self.intervals != \
                ((0, 2**self.bits_per_component - 1),) * self.components:
            res += "; intervals={}".format(self.intervals)
        return res + ">"

    @property
    def bytes_per_pixel(self):
        if self.planar:
            raise TypeError("Planar image modes do not support "
                            "bytes_per_pixel.")
        return self.components * self.bits_per_component // 8

    def get_length(self, dims):
        """Calculate the bytes needed to store an image with size ``dims``.

        :param dims: the dimensions to be used in the calculation
        :type dims: an iterable containing two integers
        :rtype: integer

        """
        if self.planar:
            x, y = dims
            return sum([
                    ((x//sub_x)*(y//sub_y)) * self.bits_per_component
                        for sub_x, sub_y in self.subsampling
                ]) // 8
        else:
            return reduce(operator.mul, dims)*self.bytes_per_pixel

    @classmethod
    def _finalize_modes(cls):
        """Link modes to their module-level names for string comparison.
        
        Once all :class:`ImageMode` s have been instantiated, they must be
        assigned ``str`` values to produce the proper comparison behavior.
        This pulls each :class:`ImageMode` instance out of ``globals()``,
        recreates it with the ``str`` value set to its variable name,
        replaces it, and adds it to a set of all available modes.

        """
        modes = set()
        for name, obj in globals().items():
            if type(obj) is cls:
                mode = str.__new__(cls, name if name != 'L32' else 'I')
                mode.__init__(obj.component_names, obj.bits_per_component,
                    obj.planar, obj.subsampling, obj.intervals)
                modes.add(mode)
                cls._create_pixel_cls(mode)
                globals()[name] = mode
        return modes
                

L = ImageMode("l")
L16 = ImageMode("l", 16)
L32 = ImageMode("l", 32)
LA = ImageMode("la")
LA32 = ImageMode("la", 16)

#L16F = ImageMode("l", 16, intervals=(0., 1.))
L32F = ImageMode("l", 32, intervals=(0., 1.))
L64F = ImageMode("l", 64, intervals=(0., 1.))
LA32F = ImageMode("la", 32, intervals=(0., 1.)*2)

RGB = ImageMode("rgb")
RGB48 = ImageMode("rgb", 16)
RGBA = ImageMode("rgba")
RGBA64 = ImageMode("rgba", 16)

#RGB48F = ImageMode("rgb", 16, intervals=(0., 1.)*3)
#RGBA64F = ImageMode("rgba", 16, intervals=(0., 1.)*4)
RGB96F = ImageMode("rgb", 32, intervals=(0., 1.)*3)
RGBA128F = ImageMode("rgba", 32, intervals=(0., 1.)*4)
RGB192F = ImageMode("rgb", 64, intervals=(0., 1.)*3)
RGBA256F = ImageMode("rgba", 64, intervals=(0., 1.)*4)

YV12 = ImageMode(("y", "cr", "cb"), planar=True,
                 subsampling=((1, 1), (2, 2), (2, 2)),
                 intervals=((16, 235), (16, 240), (16, 240)))
JPEG_YV12 = ImageMode(("y", "cr", "cb"), planar=True,
                      subsampling=((1, 1), (2, 2), (2, 2)))

#HSV = ImageMode("hsv", 16, intervals=((0., 360.), (0., 1.), (0., 1.)))
#HSL = ImageMode("hsl", 16, intervals=((0., 360.), (0., 1.), (0., 1.)))
HSV96 = ImageMode("hsv", 32, intervals=((0., 360.), (0., 1.), (0., 1.)))
HSL96 = ImageMode("hsl", 32, intervals=((0., 360.), (0., 1.), (0., 1.)))
HSV192 = ImageMode("hsv", 64, intervals=((0., 360.), (0., 1.), (0., 1.)))
HSL192 = ImageMode("hsl", 64, intervals=((0., 360.), (0., 1.), (0., 1.)))

CMYK = ImageMode("cmyk", transparent_color=(255,)*4)
CMYK64 = ImageMode("cmyk", 16, transparent_color=(65535,)*4)

MODES = ImageMode._finalize_modes()

__all__ = ["MODES"] + [name for name, value in globals().items() 
                       if isinstance(value, ImageMode)]
