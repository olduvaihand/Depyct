# depyct/image.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
"""
"""
from collections import namedtuple
from operator import index

from .image_mode import *


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
        width, height = self.size
        if self.planar:
            pass
        else:
            source = [[None for c in range(height)] for r in range(width)]
            for y, line in enumerate(self):
                for x, pixel in enumerate(line):
                    source[x][width-y] = pixel
        return Image(self.mode, source=source)

    def rotate180(self):
        """Return a new copy of the image rotated 180 degrees clockwise.
        
        """
        if self.planar:
            pass
        else:
            source = self[::-1,::-1]
        return Image(self.mode, source=source)
        
    def rotate270(self):
        """Return a new copy of the image rotated 270 degrees clockwise.
        
        """
        width, height = self.size
        if self.planar:
            pass
        else:
            source = [[None for c in range(height)] for r in range(width)]
            for y, line in enumerate(self):
                for x, pixel in enumerate(line):
                    source[width-x-1][y] = pixel
        return Image(self.mode, source=source)

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
            raise TypeError("Planar images do not support indexing "
                                 "or slicing.")
        # line
        if isinstance(key, int):
            # FIXME: update this so that it's actually returning
            #        a Line associated with this chunk of the buffer
            # bytes_per_line = self.bytes_per_pixel * self.size.width
            # start = key * bytes_per_line
            # end = start + bytes_per_line
            # return self._line_cls(self.mode,
            #                       memoryview(self.buffer[start:end]))
            return self.buffer[key]
        elif isinstance(key, slice):
            return self[::,key]
        else:
            key = tuple(key)
        if len(key) == 2 and all(isinstance(i, (int, slice)) for i in key):
            # pixel (int, int)
            if all(isinstance(i, int) for i in key):
                # FIXME: update this so that it's actually returning
                #        a Pixel associated with this chunk of the buffer
                # bytes_per_pixel = self.bytes_per_pixel
                # bytes_per_line = bytes_per_pixel * self.size.width
                # offset = bytes_per_pixel * key[0]
                # start = key[1] * bytes_per_line + offset
                # end = start + bytes_per_pixel
                # return self._pixel_cls(self.mode,
                #                        memoryview(self.buffer[start:end]))
                return self.buffer[key[0]][key[1]]
            # image (slice, slice)
            if all(isinstance(i, slice) for i in key):
                # FIXME: this should be copying the data
                #        not just getting lines
                source = []
                for line in self.buffer[key[1]]:
                    source.append(line[key[0]])
            # horizontal image (width =  (slice, int)
            elif isinstance(key[0], slice):
                # FIXME: this should be copying the data
                #        not just getting lines
                source = [self[key[1]][key[0]]]
            # vertical image (int, slice)
            else: #elif isinstance(key[0], int):
                # FIXME: this should be copying the data
                #        not just getting lines
                source = []
                for line in self[key[1]]:
                    source.append([line[key[0]]])
            return Image(self.mode, source=source)
        else:
            raise TypeError("Image indices must be int, slice, or a "
                            "two-tuple composed of ints, slices, or both.")

    def __setitem__(self, key, value):
        """
        """
        if self.planar:
            raise TypeError("Planar images do not support indexing or "
                            "slicing.")


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
