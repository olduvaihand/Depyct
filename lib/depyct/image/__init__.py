# depyct/image/__init__.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
"""
"""
from collections import namedtuple
import ctypes
from operator import index
import os
from struct import Struct
import warnings

from .mode import *
from .line import Line
from depyct import util


__all__ = ["ImageSize", "ImageMixin", "Image"]

if util.py3k:
    long = int


class _Image(ctypes.Structure):
    _pack_ = 1


class ImageSize(namedtuple("ImageSize", "width height")):
    """ImageSize is a helper class that represents the 2-dimensional size
    of an image.  Generally, it isn't necessary for a user to create
    ImageSize objects, as they are automatically generated on initialization
    of an :class:`~image.Image` object and cannot be modified once set.

    :param width: An integral value or an object that supports an
        __index__ method.
    :param height: An integral value or an object that supports an
        __index__ method.

    """

    def __new__(cls, width, height):
        if width <= 0:
            raise ValueError("width must be greater than 0")
        try:
            width = index(width)
        except TypeError:
            raise TypeError("width must be of integral value or provide "
                            "an __index__ method")
        if height <= 0:
            raise ValueError("height must be greater than 0")
        try:
            height = index(height)
        except TypeError:
            raise TypeError("height must be of integral value or provide "
                            "an __index__ method")
        return super(ImageSize, cls).__new__(cls, width, height)

    @staticmethod
    def must_be_equal(func):
        def f(self, other):
            if self.size == other.size and self.mode is other.mode:
                return func(self, other)
            raise ValueError("Images must be the same size and have the same "
                             "mode.  Received {} and {}.".format(self, other))
        return f


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
            raise NotImplementedError("rotate90() is not implemented for "
                                      "planar images.")
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
            raise NotImplementedError("rotate180() is not implemented for "
                                      "planar images.")
        else:
            return self[::-1, ::-1]
        
    def rotate270(self):
        """Return a new copy of the image rotated 270 degrees clockwise.
        
        """
        new_height, new_width = self.size
        if self.planar:
            raise NotImplementedError("rotate270() is not implemented for "
                                      "planar images.")
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
        raise NotImplementedError("split() is not yet implemented.")
        if self.planar:
            pass
        else:
            # determine proper mode for each channel
            # create mode.components images of size == self.size
            return tuple(self[::,::,i] for i in range(self.components))

    def pixels(self):
        """pixels() -> iterator[pixel]

        """
        if self.planar:
            raise TypeError("Planar images do not provide a pixels "
                            "iterator method.")
        for line in self:
            for pixel in line:
                yield pixel

    def __iter__(self):
        """__iter__() -> iterator[line]

        """
        if self.planar:
            raise TypeError("Planar images do not support iteration.")
        for l in self.lines:
            yield l

    def __len__(self):
        """__len__() -> int

        """
        if self.planar:
            raise TypeError("Planar images do not have a length.")
        return self.size.height

    # FIXME:
    # Planar images must include component images accessible via
    # component names.  These images are single component images
    # whose buffers are the regions of the main image buffer corresponding
    # to their respective components.  (I.e. changes made to the component
    # images will be immediately reflected in the parent image and vice versa)

    def __getitem__(self, key):
        """__getitem__(self, integer) -> line
        __getitem__(self, tuple[integer]) -> pixel
        __getitem__(self, slice | tuple[integer | slice]) -> image

        """
        if self.planar:
            raise TypeError("Planar images do not support indexing or "
                            "slicing.")
        # line
        if isinstance(key, (int, long)):
            if key < 0:
                key += self.size.height
            if key >= self.size.height:
                raise IndexError("Line index out of range.")
            return self.lines[key]
        elif isinstance(key, slice):
            #key = (slice(), key)
            return self[::, key]
        else:
            key = tuple(key)
        if len(key) == 2 and all(isinstance(i, (int, long, slice)) for i in key):
            # pixel (int, int)
            # horizontal image (slice, int)
            # FIXME: let's see if we can do this without calling into 
            #        __getitem__ again
            if isinstance(key[1], (int, long)):
                return self[key[1]][key[0]]
            # image (slice, slice)
            # vertical image (int, slice)
            else:
                pixel_idx = key[0]
                if isinstance(pixel_idx, (int, long)):
                    if pixel_idx < 0:
                        pixel_idx += self.size.width
                    if pixel_idx > self.size.width:
                        raise IndexError("Pixel index out of range.")
                    pixel_idx = slice(pixel_idx, pixel_idx + 1)
                l_start, l_stop, l_step = key[1].indices(self.size.height)
                width = len(range(*pixel_idx.indices(self.size.width)))
                height = len(range(l_start, l_stop, l_step))
                res = Image(self.mode, size=(width, height))
                for i, l in enumerate(self.lines[key[1]]):
                    res[i] = l[pixel_idx]
                return res
        raise TypeError("Image indices must be int, slice, or a "
                        "2-tuple composed of ints, slices, or both.")

    def __setitem__(self, key, value):
        """
        """
        if self.planar:
            raise TypeError("Planar images do not support indexing or "
                            "slicing.")
        if isinstance(key, (int, long)):
            if key < 0:
                key += self.size.height
            if key >= self.size.height:
                raise IndexError("Line index out of range.")
            # maybe have something that lets us do this with things that
            # aren't images
            if isinstance(value, ImageMixin):
                assert (value.size.height == 1 and
                        value.size.width == self.size.width)
            else:
                assert len(value) == self.size.width
            self[key][:] = value[0]
            return
        elif isinstance(key, slice):
            #key = slice(), key
            self[::, key] = value
            return
        else:
            key = tuple(key)
        if len(key) == 2 and all(isinstance(i, (int, long, slice)) for i in key):
            # pixel (int, int)
            if all(isinstance(i, (int, long)) for i in key):
                self.lines[key[1]][key[0]].value = value
            # horizontal image (slice, int)
            elif isinstance(key[1], (int, long)):
                self.lines[key[1]][key[0]] = value[0]
            # image (slice, slice)
            # vertical image (int, slice)
            else:
                pixel_idx = key[0]
                if isinstance(pixel_idx, (int, long)):
                    if pixel_idx < 0:
                        pixel_idx += self.size.width
                    if pixel_idx > self.size.width:
                        raise IndexError("Pixel index out of range.")
                    pixel_idx = slice(pixel_idx, pixel_idx + 1)
                l_start, l_stop, l_step = key[1].indices(self.size.height)
                height = len(range(l_start, l_stop, l_step))
                # maybe have something that lets us do this with things that
                # aren't images
                # do we need to check on the width of each line?
                # if we do, calculate the width of a line
                #    1 if key[0] isinstance int,
                #    len(range(key[0].indices(self.size.width))) if key[0] isinstance slice
                assert height == len(value)
                for line, values in zip(self.lines[key[1]], value):
                    line[pixel_idx] = values
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
        """
        ``mode`` must be one of the constants in the ``MODES`` set,

        ``size`` is a sequence of two integers (width and height of the new image);
        
        ``color`` is a sequence of integers, one for each
        component of the image, used to initialize all the pixels to the
        same value;
        
        ``source`` can be a sequence of integers of the appropriate size and format
        that is copied as-is in the buffer of the new image or an existing image;
        
        in Python 2.x ``source`` can also be an instance of ``str`` and is interpreted
        as a sequence of bytes.
        
        ``color`` and ``source`` are mutually exclusive and if
        they are both omitted the image is initialized to transparent
        black (all the bytes in the buffer have value 16 in the ``YV12``
        mode, 255 in the ``CMYK*`` modes and 0 for everything else). 
        
        If ``source`` is present and is an image, ``mode`` and/or ``size``
        can be omitted; if they are specified and are different from the
        source mode and/or size, the source image is converted.
        """
        self._mode = None
        self._size = None
        self._buffer = None
        self.info = {}

        if mode is not None:
            if mode not in MODES:
                raise ValueError("{} is not a valid mode.".format(mode))
            self._mode = mode

        if size is not None:
            try:
                self._size = ImageSize(*size)
            except:
                raise ValueError("size must be an iterable returning 2 "
                                 "elements, not {}".format(size))

        if source:
            # TODO: deal with source having a value
            if color:
                warnings.warn("color is disregarded when source is not None.")
            if isinstance(source, ImageMixin):
                if size:
                    if size != source.size:
                        # deal with resizing
                        pass
                    else:
                        pass
                else:
                    self._size = source.size
                if mode is None:
                    self._mode = source.mode
                else:
                    # deal with converting color
                    pass
            else:
                # source had better be an iterable that we can stuff 
                # into a buffer
                # python2 supports a byte string
                if util.py27 and isinstance(source, str):
                    pass
        elif size and mode:

            assert self.size.width % self.mode.x_divisor == 0
            assert self.size.height % self.mode.y_divisor == 0

            if color and len(color) != self.components:
                raise ValueError("color must be an iterable with {} values, "
                                 "one for each component in {}.".format(
                                     self.components, self.mode))
            # initialize buffer to the correct size and color
            _buffer = util.initialize_buffer(mode, size, color)

            # TODO: externalize this structure building stuff
            line_struct = type("LineBuffer", (Line,), {
                    "_fields_": [("pixels", mode.pixel_cls*self.size.width)],
                    "image_cls": self.__class__,
                    "mode": self.mode
                })

            image_struct = type("ImageBuffer", (_Image,),
                    {"_fields_": [("lines", line_struct*self.size.height)]})

            self._image_data = image_struct.from_buffer(_buffer)
            self._buffer = memoryview(_buffer)

        else:
            raise ValueError("You must minimally specify a source from "
                             "which to build the image or a mode and size "
                             "with which to initialize the buffer.")

    @property
    def lines(self):
        return self._image_data.lines

    def __str__(self):
        return "{}(mode={}, size={})".format(self.__class__.__name__,
                                             self.mode, self.size)

    if util.py27:
        def __unicode__(self):
            return unicode(str(self))

    def __repr__(self):
        lines = []
        for line in self:
            lines.append("\t" + " ".join(str(p.value) for p in line))
        return "{}<\n{}\n>".format(self.__class__.__name__,
                "\n".join(lines))

    @util.readonly_property
    def buffer(self):
        return self._buffer

    @util.readonly_property
    def size(self):
        return self._size

    @util.readonly_property
    def mode(self):
        return self._mode

    @classmethod
    def open(cls, filename, **options):
        from depyct.io.format import registry

        ext = os.path.splitext(filename)[1][1:]
        try:
            format = registry[ext](cls, **options)
        except KeyError:
            raise IOError("{} is not a recognized image format.".format(ext))
        return format.open(cls, filename)

    def save(self, filename, **options):
        from depyct.io.format import registry

        ext = os.path.splitext(filename)[1][1:]
        try:
            format = registry[ext](self.__class__, **options)
        except KeyError:
            raise IOError("{} is not a recognized image format.".format(ext))
        return format.save(self, filename)

    @ImageSize.must_be_equal
    def __lt__(self, other):
        for y in range(self.size.height):
            for x in range(self.size.width):
                if self[x,y].value >= other[x,y].value:
                    return False
        return True

    @ImageSize.must_be_equal
    def __le__(self, other):
        for y in range(self.size.height):
            for x in range(self.size.width):
                if self[x,y].value > other[x,y].value:
                    return False
        return True

    @ImageSize.must_be_equal
    def __eq__(self, other):
        for y in range(self.size.height):
            for x in range(self.size.width):
                if self[x,y].value != other[x,y].value:
                    return False
        return True

    @ImageSize.must_be_equal
    def __ne__(self, other):
        for y in range(self.size.height):
            for x in range(self.size.width):
                if self[x,y].value == other[x,y].value:
                    return False
        return True

    @ImageSize.must_be_equal
    def __ge__(self, other):
        for y in range(self.size.height):
            for x in range(self.size.width):
                if self[x,y].value < other[x,y].value:
                    return False
        return True

    @ImageSize.must_be_equal
    def __gt__(self, other):
        for y in range(self.size.height):
            for x in range(self.size.width):
                if self[x,y].value <= other[x,y].value:
                    return False
        return True

    def __hash__(self):
        pass

    def __nonzero__(self):
        transparent_color = self.mode.transparent_color
        if any(p.value != transparent_color for p in self.pixels()):
            return False
        return True

    def __add__(self, other):
        pass

    def __sub__(self, other):
        pass

    def __mul__(self, other):
        pass

    def __floordiv__(self, other):
        pass

    def __mod__(self, other):
        pass

    def __divmod__(self, other):
        pass

    def __pow__(self, other, modulo=None):
        pass

    def __lshift__(self, other):
        pass

    def __rshift__(self, other):
        pass

    def __and__(self, other):
        pass

    def __xor__(self, other):
        pass

    def __or__(self, other):
        pass

    def __div__(self, other):
        pass

    def __truediv__(self, other):
        pass

    def __radd__(self, other):
        pass

    def __rsub__(self, other):
        pass

    def __rmul__(self, other):
        pass

    def __rfloordiv__(self, other):
        pass

    def __rmod__(self, other):
        pass

    def __rdivmod__(self, other):
        pass

    def __rpow__(self, other, modulo=None):
        pass

    def __rlshift__(self, other):
        pass

    def __rrshift__(self, other):
        pass

    def __rand__(self, other):
        pass

    def __rxor__(self, other):
        pass

    def __ror__(self, other):
        pass

    def __iadd__(self, other):
        pass

    def __isub__(self, other):
        pass

    def __imul__(self, other):
        pass

    def __ifloordiv__(self, other):
        pass

    def __imod__(self, other):
        pass

    def __idivmod__(self, other):
        pass

    def __ipow__(self, other, modulo=None):
        pass

    def __ilshift__(self, other):
        pass

    def __irshift__(self, other):
        pass

    def __iand__(self, other):
        pass

    def __ixor__(self, other):
        pass

    def __ior__(self, other):
        pass

    def __neg__(self):
        pass

    def __pos__(self):
        pass

    def __abs__(self):
        pass

    def __invert__(self):
        pass
