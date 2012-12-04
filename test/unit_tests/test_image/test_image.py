# test/unit_tests/test_image/test_image.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
from depyct.testing import DepyctUnitTest
from depyct.image import Image
from depyct.image.line import Line
from depyct.image.pixel import Pixel
from depyct.image.mode import RGB, YV12


class NonPlanarImageTest(DepyctUnitTest):

    def setUp(self):
        width, height = 2, 3
        self.im = Image(RGB, size=(width, height))
        for y, line in enumerate(self.im):
            for x, pixel in enumerate(line):
                pixel.value = (y * width + x,) * self.im.components

    def test_components(self):
        self.assertEqual(self.im.components, RGB.components)

    def test_component_names(self):
        self.assertEqual(self.im.component_names, RGB.component_names)

    def test_bits_per_component(self):
        self.assertEqual(self.im.bits_per_component, RGB.bits_per_component)

    def test_bytes_per_pixel(self):
        self.assertEqual(self.im.bytes_per_pixel, RGB.bytes_per_pixel)

    def test_intervals(self):
        self.assertEqual(self.im.intervals, RGB.intervals)

    def test_planar(self):
        self.assertEqual(self.im.planar, RGB.planar)

    def test_subsampling(self):
        self.assertEqual(self.im.intervals, RGB.intervals)

    def test_map_with_one_function(self):
        expected = ((0, 0, 0), (2, 2, 2),
                    (4, 4, 4), (6, 6, 6),
                    (8, 8, 8), (10, 10, 10))
        self.im.map(lambda c: 2*c)
        self.assertEqual(expected, tuple(p.value for p in self.im.pixels()))

    def test_map_with_two_functions(self):
        expected = ((1, 0, 0), (1, 2, 1),
                    (1, 4, 2), (1, 6, 3),
                    (1, 8, 4), (1, 10, 5))
        self.im.map(lambda r: 1, lambda g: 2*g)
        self.assertEqual(expected, tuple(p.value for p in self.im.pixels()))

    def test_map_with_three_functions(self):
        expected = ((1, 2, 3), (1, 2, 3),
                    (1, 2, 3), (1, 2, 3),
                    (1, 2, 3), (1, 2, 3))
        self.im.map(lambda r: 1, lambda g: 2, lambda b: 3)
        self.assertEqual(expected, tuple(p.value for p in self.im.pixels()))

    def test_map_with_too_many_functions(self):
        with self.assertRaises(ValueError):
            self.im.map(lambda r: 1, lambda g: 2, lambda b: 3, lambda a: 4)

    def test_map_with_named_function(self):
        expected = ((0, 0, 0), (1, 2, 1),
                    (2, 4, 2), (3, 6, 3),
                    (4, 8, 4), (5, 10, 5))
        self.im.map(g=lambda g: 2*g)
        self.assertEqual(expected, tuple(p.value for p in self.im.pixels()))

    def test_map_with_two_named_functions(self):
        expected = ((0, 0, 0), (1, 2, 3),
                    (2, 4, 6), (3, 6, 9),
                    (4, 8, 12), (5, 10, 15))
        self.im.map(b=lambda b: 3*b, g=lambda g: 2*g)
        self.assertEqual(expected, tuple(p.value for p in self.im.pixels()))

    def test_map_with_three_named_functions(self):
        expected = ((0, 0, 0), (0, 2, 3),
                    (0, 4, 6), (0, 6, 9),
                    (0, 8, 12), (0, 10, 15))
        self.im.map(b=lambda b: 3*b, r=lambda r: 0*r, g=lambda g: 2*g)
        self.assertEqual(expected, tuple(p.value for p in self.im.pixels()))

    def test_map_with_too_many_named_functions(self):
        with self.assertRaises(NameError):
            f = lambda i: 1
            self.im.map(r=f, g=f, b=f, a=f)

    def test_rotate90(self):
        expected = ((4, 4, 4), (2, 2, 2), (0, 0, 0),
                    (5, 5, 5), (3, 3, 3), (1, 1, 1))
        rot90 = self.im.rotate90()
        self.assertEqual(rot90.size, self.im.size[::-1])
        self.assertEqual(expected, tuple(p.value for p in rot90.pixels()))

    def test_rotate180(self):
        expected = ((5, 5, 5), (4, 4, 4),
                    (3, 3, 3), (2, 2, 2),
                    (1, 1, 1), (0, 0, 0))
        rot180 = self.im.rotate180()
        self.assertEqual(rot180.size, self.im.size)
        self.assertEqual(expected, tuple(p.value for p in rot180.pixels()))

    def test_rotate270(self):
        expected = ((1, 1, 1), (3, 3, 3), (5, 5, 5),
                    (0, 0, 0), (2, 2, 2), (4, 4, 4))
        rot270 = self.im.rotate270()
        self.assertEqual(rot270.size, self.im.size[::-1])
        self.assertEqual(expected, tuple(p.value for p in rot270.pixels()))

    def test_clip(self):
        expected = tuple(p.value for p in self.im.pixels())
        self.im.clip()
        self.assertEqual(expected, tuple(p.value for p in self.im.pixels()))

    def test_split(self):
        pass

    def test_pixels(self):
        expected = ((0, 0, 0), (1, 1, 1),
                    (2, 2, 2), (3, 3, 3),
                    (4, 4, 4), (5, 5, 5))
        self.assertEqual(expected, tuple(p.value for p in self.im.pixels()))

    def test___iter__(self):
        c = 0
        for line in self.im:
            c += 1
            self.assertTrue(isinstance(line, Line))
        self.assertEqual(c, self.im.size.height)

    def test___len__(self):
        self.assertEqual(len(self.im), self.im.size.height)

    def test___getitem__int(self):
        res = self.im[0]
        self.assertTrue(isinstance(res, Line))
        self.assertEqual(((0, 0, 0), (1, 1, 1)), tuple(p.value for p in res))

    def test___getitem__slice(self):
        pass

    def test___getitem__int_int(self):
        res = self.im[0,0]
        self.assertTrue(isinstance(res, Pixel))
        self.assertEqual((0, 0, 0), res.value)

    def test___getitem__int_slice(self):
        pass

    def test___getitem__slice_int(self):
        pass

    def test___getitem__slice_slice(self):
        pass

    def test___setitem__(self):
        pass


class PlanarImageTest(DepyctUnitTest):

    def setUp(self):
        self.im = Image(YV12, size=(2, 2))

    def test_components(self):
        pass

    def test_component_names(self):
        pass

    def test_bits_per_component(self):
        pass

    def test_bytes_per_pixel(self):
        pass

    def test_intervals(self):
        pass

    def test_planar(self):
        pass

    def test_subsampling(self):
        pass

    def test_map(self):
        pass

    def test_rotate90(self):
        pass

    def test_rotate180(self):
        pass

    def test_rotate270(self):
        pass

    def test_clip(self):
        pass

    def test_split(self):
        pass

    def test_pixels(self):
        with self.assertRaises(TypeError):
            for pixel in self.im.pixels():
                pass

    def test___iter__(self):
        with self.assertRaises(TypeError):
            for line in self.im:
                pass

    def test___len__(self):
        with self.assertRaises(TypeError):
            len(self.im)

    def test___getitem__(self):
        with self.assertRaises(TypeError):
            self.im[0]
        with self.assertRaises(TypeError):
            self.im[0,0]
        with self.assertRaises(TypeError):
            self.im[0:1]
        with self.assertRaises(TypeError):
            self.im[0:1,0:1]

    def test___setitem__(self):
        with self.assertRaises(TypeError):
            self.im[0] = 1
        with self.assertRaises(TypeError):
            self.im[0,0] = 1
        with self.assertRaises(TypeError):
            self.im[0:1] = 1
        with self.assertRaises(TypeError):
            self.im[0:1,0:1] = 1
