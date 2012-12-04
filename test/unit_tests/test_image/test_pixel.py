# test/unit_tests/test_image/test_pixel.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
from array import array

from depyct.image.mode import *
from depyct.testing import DepyctUnitTest
from depyct import util


class PixelTest(DepyctUnitTest):

    @classmethod
    def setupClass(cls):
        cls.pixels = {}
        for mode in MODES:
            buffer = util.initialize_buffer(mode, (1, 1))
            cls.pixels[mode] = mode.pixel_cls(buffer)

    def test_component_properties(self):
        for mode, pixel in self.pixels.items():
            for component in mode.component_names:
                self.assertTrue(hasattr(pixel, component), 
                        "Pixel classes should provide component access.")

    def test___iter__(self):
        for mode, pixel in self.pixels.items():
            self.assertEqual(mode.transparent_color, tuple(pixel), 
                    "Pixel.__iter__() yields the elements of the pixel.")

    def test___getitem__with_int(self):
        for mode, pixel in self.pixels.items():
            self.assertEqual(pixel[0], mode.transparent_color[0],
                    "Pixel.__getitem__(int) returns the component at index "
                    "`int`.")

    def test___getitem__with_slice(self):
        for mode, pixel in self.pixels.items():
            self.assertEqual(pixel[:], mode.transparent_color[:],
                    "Pixel.__getitem__(slice) returns the components at slice "
                    "`slice`.")

    def test___getitem__with_negative_indices(self):
        for mode, pixel in self.pixels.items():
            self.assertEqual(pixel[-1], mode.transparent_color[-1],
                    "Pixel.__getitem__(-int) returns the components at index "
                    "`-int`.")

    def test___getitem__with_out_of_range_indices(self):
        for mode, pixel in self.pixels.items():
            with self.assertRaises(IndexError):
                pixel[10]
            with self.assertRaises(IndexError):
                pixel[-10]

    def test___setitem__with_int(self):
        for mode, pixel in self.pixels.items():
            pass

    def test___setitem__with_slice(self):
        for mode, pixel in self.pixels.items():
            pass

    def test___setitem__with_negative_indices(self):
        for mode, pixel in self.pixels.items():
            pass

    def test___setitem__with_out_of_range_indices(self):
        for mode, pixel in self.pixels.items():
            pass


class ComponentPropertyTest(DepyctUnitTest):
    pass


class PixelValuePropertyTest(DepyctUnitTest):
    pass


class StructPixelValuePropertyTest(DepyctUnitTest):
    pass


class PixelMakerTest(DepyctUnitTest):
    pass
