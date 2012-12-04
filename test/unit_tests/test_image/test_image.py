# test/unit_tests/test_image/test_image.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
from depyct.testing import DepyctUnitTest
from depyct.image import Image
from depyct.image.mode import RGB, YV12


class NonPlanarImageTest(DepyctUnitTest):

    def setUp(self):
        self.im = Image(RGB, size=(2, 2))

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
        pass

    def test___iter__(self):
        pass

    def test___len__(self):
        pass

    def test___getitem__(self):
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
