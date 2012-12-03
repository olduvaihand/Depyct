# depyct/image/__init__.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
"""
"""
from collections import namedtuple
from operator import index
from struct import Struct

from .mode import *
from .line import Line
from .. import util


__all__ = ["ImageSize", "ImageMixin", "Image"]


class ImageSize(namedtuple("_ImageSize", "width height")):
    """ImageSize is a helper class that represents the 2-dimensional size
    of an image.  Generally, it isn't necessary for a user to create
    ImageSize objects, as they are automatically generated on initialization
    of an :class:`~image.Image` object and cannot be modified once set.

    :param width: An integral value or an object that supports an
        __index__ method.
    :param height: An integral value or an object that supports an
        __index__ method.

    """

    def __init__(self, width, height):
        if width <= 0:
            raise ValueError("width must be greater than 0")
        if height <= 0:
            raise ValueError("height must be greater than 0")
        try:
            width = index(width)
        except TypeError:
            raise TypeError("width must be of integral value or provide "
                            "an __index__ method")
        try:
            height = index(height)
        except TypeError:
            raise TypeError("height must be of integral value or provide "
                            "an __index__ method")
        super(ImageSize, self).__init__(width, height)

    def __repr__(self):
        return "ImageSize(width=%d, height=%d)" % (self.width, self.height)


class ImageMixin(object):
    """

    """

    @property
    def components(self):
        return self.mode.components

    @property
    def component_names(self):
        return self.mode.component_names

    @property
    def bits_per_component(self):
        return self.mode.bits_per_component

    @property
    def bytes_per_pixel(self):
        return self.mode.bytes_per_pixel

    @property
    def intervals(self):
        return self.mode.intervals

    @property
    def planar(self):
        return self.mode.planar

    @property
    def subsampling(self):
        return self.mode.subsampling

    def map(self, *filters, **named_filters):
        """Apply one or more channel filters to the image.  Each filter should
        be a function taking a single argument, and filters should be given
        in the same order as the channels in the image.  
       
        If only one filter is provided, the filter will be applied to all 
        channels.

        If the number of filters provided is greater than one but less than
        the number of channels, a no-op filter will be applied to the remaining
        channels.

        Examples:

        To zero out the green channel of an RGB image, you could:

            im.map(lambda r: r, lambda g: 0)
            # which is equivalent to 
            im.map(lambda r: r, lambda g: 0, lambda b: b)
        
        map(function[, function...]) -> None

        """
        components = self.components
        if len(filters) > self.components:
            raise ValueError(
                    "The number of filters passed cannot exceed the number of "
                    "components in the image ({})".format(self.components)
                )

        filters = list(filters)
        if len(filters) == 1:
            filters = filters * components
        else:
            filters = filters + ([lambda x: x] * (components-len(filters)))

        # named_filters override filters
        for name, filter in named_filters.items():
            if name not in self.component_names:
                raise NameError(
                        "{} is not a valid component name for an image with "
                        "components {}".format(name,
                                               ", ".join(self.component_names))
                    )
            filters[self.component_names.index(name)] = filter

        if self.planar:
            pass
        else:
            for pixel in self.pixels():
                pixel[:] = [filters[i](pixel[i]) for i in range(components)]

    def rotate90(self):
        """Return a new copy of the image rotated 90 degrees clockwise.
        
        """
        new_height, new_width = self.size
        if self.planar:
            raise NotImplemented("rotate90() is not implemented for planar "
                                 "images.")
        else:
            res = Image(self.mode, size=(new_width, new_height))
            for x, line in enumerate(self):
                for y, pixel in enumerate(line):
                    res[new_width-x-1, y] = pixel.value
        return res

    def rotate180(self):
        """Return a new copy of the image rotated 180 degrees clockwise.
        
        """
        if self.planar:
            raise NotImplemented("rotate180() is not implemented for planar "
                                 "images.")
        else:
            return self[::-1, ::-1]
        
    def rotate270(self):
        """Return a new copy of the image rotated 270 degrees clockwise.
        
        """
        new_height, new_width = self.size
        if self.planar:
            raise NotImplemented("rotate270() is not implemented for planar "
                                 "images.")
        else:
            res = Image(self.mode, size=(new_width, new_height))
            for x, line in enumerate(self):
                for y, pixel in enumerate(line):
                    res[x, new_height-y-1] = pixel.value
        return res

    def clip(self):
        """Saturate invalid component values in planar images to the minimum or
        maximum allowed.

        """
        if not self.planar:
            return
        for i in range(self.components):
            low, high = self.mode.intervals[i]
            # how do you extract the plane without creating a new image?
            plane = []
            for value in plane:
                value = min(max(value, low), high)

    def split(self):
        """Return a tuple of L, L16, or L32 images corresponding to the
        individual components.

        """
        raise NotImplemented("split() is not yet implemented.")
        if self.planar:
            pass
        else:
            return tuple(self[::,::,i] for i in range(self.components))

    def pixels(self):
        """pixels() -> iterator[pixel]

        """
        if self.planar:
            raise TypeError("Planar images do not provide a pixels "
                            "iterator method.")
        for row in self:
            for pixel in row:
                yield pixel

    def __iter__(self):
        """__iter__() -> iterator[line]

        """
        if self.planar:
            raise TypeError("Planar images do not support iteration.")
        for i in range(len(self)):
            yield self[i]

    def __len__(self):
        """__len__() -> int

        """
        if self.planar:
            raise TypeError("Planar images do not have a length.")
        return self.size.height

    def __getitem__(self, key):
        """__getitem__(self, integer) -> line
        __getitem__(self, tuple[integer]) -> pixel
        __getitem__(self, slice | tuple[integer | slice]) -> image

        """
        if self.planar:
            raise TypeError("Planar images do not support indexing or "
                            "slicing.")
        # line
        if isinstance(key, int):
            if key < 0:
                key += self.height
            bytes_per_line = self.mode.bytes_per_pixel * self.width
            start = key * bytes_per_line
            end = start + bytes_per_line
            return Line(self.mode, self.buffer[start:end])
        elif isinstance(key, slice):
            return self[::, key]
        else:
            key = tuple(key)
        if len(key) == 2 and all(isinstance(i, (int, slice)) for i in key):
            # pixel (int, int)
            # horizontal image (slice, int)
            if isinstance(key[1], int):
                return self[key[1]][key[0]]
            # image (slice, slice)
            # vertical image (int, slice)
            else:
                pixel_idx = key[0]
                if isinstance(pixel_idx, int):
                    if pixel_idx < 0:
                        pixel_idx += self.width
                    pixel_idx = slice(pixel_idx, pixel_idx + 1)
                l_start, l_stop, l_step = key[1].indices(self.height)
                width = len(range(*pixel_idx.indices(self.width)))
                height = len(range(l_start, l_stop, l_step))
                res = Frame(self.mode, size=(width, height),
                            buffer=init_buffer(self.mode, (width, height)))
                for i, l in enumerate(range(l_start, l_stop, l_step)):
                    res[i] = self[l][pixel_idx]
                return res
        raise TypeError("Image indices must be int, slice, or a "
                        "2-tuple composed of ints, slices, or both.")

    def __setitem__(self, key, value):
        """
        """
        if self.planar:
            raise TypeError("Planar images do not support indexing or "
                            "slicing.")
        if isinstance(key, int):
            line = self[key]
            assert (value.height == 1 and value.width == self.width)
            line[:] = value[0]
            return
        elif isinstance(key, slice):
            self[::, key] = value
            return
        else:
            key = tuple(key)
        if len(key) == 2 and all(isinstance(i, (int, slice)) for i in key):
            # pixel (int, int)
            if all(isinstance(i, int) for i in key):
                # pixel = self[key]
                self[key].value = value
            # horizontal image (slice, int)
            elif isinstance(key[1], int):
                # line = self[key[1]]
                self[key[1]][key[0]] = value[0]
            # image (slice, slice)
            # vertical image (int, slice)
            else:
                pixel_idx = key[0]
                if isinstance(pixel_idx, int):
                    if pixel_idx < 0:
                        pixel_idx += self.width
                    pixel_idx = slice(pixel_idx, pixel_idx + 1)
                l_start, l_stop, l_step = key[1].indices(self.height)
                height = len(range(l_start, l_stop, l_step))
                assert height == value.height
                for i, values in zip(range(l_start, l_stop, l_step), value):
                    #line = self[i]
                    self[i][pixel_idx] = values
        else:
            raise TypeError("Image indices must be int, slice, or a "
                            "2-tuple composed of ints, slices, or both.")

            
class Image(ImageMixin):
    """
    :attr:`mode`
        The image mode.

    :attr:`size`
        An instance of :class:`ImageSize`

    :attr:`buffer`
        A sequence of bytes.
    
    :attr:`info`
        A dict object that can contain arbitrary metadata associated with the
        image.
    """

    def __init__(self, mode=None, size=None, color=None, source=None):

        if isinstance(source, ImageMixin):
            # if mode is None:
            #     mode = source.mode
            # if size is None:
            #     size = source.size
            # 
            # 
            # 

            pass

        if source is not None and color is not None:
            raise ValueError("source and color cannot be specified "
                             "simultaneously.")

        if mode is not None and mode not in MODES:
            raise ValueError("{} is not a valid mode.".format(mode))

        self.mode = mode
        self._size = ImageSize(*size)
        self.color = color
        self.info = {}
        self.buffer = None
        # assert self.size.width % self.mode.x_divisor == 0
        # assert self.size.height % self.mode.y_divisor == 0
        # buffer_size = mode.get_length(self.size)

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self):
        raise TypeError("size is a read-only value.")
