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


class Image(ImageMixin):
    """
    """
