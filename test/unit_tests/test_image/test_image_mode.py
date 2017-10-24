# test/unit_tests/test_image/test_image_mode.py
# Copyright (c) 2012-2017 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
from depyct import testing
from depyct.image import mode


class ImageModeTest(testing.DepyctUnitTest):

    @classmethod
    def setUpClass(cls):
        cls.bytes_per_pixel = {
                mode.L: 1,
                mode.L16: 2,
                mode.L32: 4,
                mode.LA: 2,
                mode.LA32: 4,
                #mode.L16F: 2,
                mode.L32F: 4,
                mode.L64F: 8,
                mode.LA32F: 8,
                mode.RGB: 3,
                mode.RGB48: 6,
                mode.RGBA: 4,
                mode.RGBA64: 8,
                #mode.RGB48F: 6,
                #mode.RGBA64F: 8,
                mode.RGB96F: 12,
                mode.RGBA128F: 16,
                mode.RGB192F: 24,
                mode.RGBA256F: 32,
                #mode.HSV: 6,
                #mode.HSL: 6,
                mode.HSV96: 12,
                mode.HSL96: 12,
                mode.HSV192: 24,
                mode.HSL192: 24,
                mode.CMYK: 4,
                mode.CMYK64: 8,
            }

    def test_is_float(self):
        float_modes = {#mode.L16F,
                       mode.L32F, mode.L64F, mode.LA32F,
                       #mode.RGB48F, mode.RGBA64F, 
                       mode.RGB96F, mode.RGBA128F, mode.RGB192F, mode.RGBA256F,
                       mode.HSV96, mode.HSL96, mode.HSV192, mode.HSL192}
        for m in float_modes:
            self.assertTrue(m._is_float)
        for m in mode.MODES:
            if m not in float_modes:
                self.assertFalse(m._is_float)

    def test_bytes_per_pixel(self):
        for m, bytes_per_pixel in self.bytes_per_pixel.items():
            self.assertEqual(m.bytes_per_pixel, bytes_per_pixel)

        with self.assertRaises(TypeError):
            mode.YV12.bytes_per_pixel
        with self.assertRaises(TypeError):
            mode.JPEG_YV12.bytes_per_pixel

    def test_get_length(self):
        for m, bytes_per_pixel in self.bytes_per_pixel.items():
            self.assertEqual(m.get_length((10, 10)), 100*bytes_per_pixel)

        self.assertEqual(mode.YV12.get_length((10, 10)), 150)
        self.assertEqual(mode.JPEG_YV12.get_length((10, 10)), 150)

    def test_string_equality(self):
        self.assertEqual(mode.L16, "L16")
        self.assertEqual(mode.L32, "I")
        self.assertEqual(mode.LA, "LA")
        self.assertEqual(mode.LA32, "LA32")
        #self.assertEqual(mode.L16F, "L16F")
        self.assertEqual(mode.L32F, "L32F")
        self.assertEqual(mode.L64F, "L64F")
        self.assertEqual(mode.LA32F, "LA32F")
        self.assertEqual(mode.RGB, "RGB")
        self.assertEqual(mode.RGB48, "RGB48")
        self.assertEqual(mode.RGBA, "RGBA")
        self.assertEqual(mode.RGBA64, "RGBA64")
        #self.assertEqual(mode.RGB48F, "RGB48F")
        #self.assertEqual(mode.RGBA64F, "RGBA64F")
        self.assertEqual(mode.RGB96F, "RGB96F")
        self.assertEqual(mode.RGBA128F, "RGBA128F")
        self.assertEqual(mode.RGB192F, "RGB192F")
        self.assertEqual(mode.RGBA256F, "RGBA256F")
        self.assertEqual(mode.YV12, "YV12")
        self.assertEqual(mode.JPEG_YV12, "JPEG_YV12")
        #self.assertEqual(mode.HSV, "HSV")
        #self.assertEqual(mode.HSL, "HSL")
        self.assertEqual(mode.HSV96, "HSV96")
        self.assertEqual(mode.HSL96, "HSL96")
        self.assertEqual(mode.HSV192, "HSV192")
        self.assertEqual(mode.HSL192, "HSL192")
        self.assertEqual(mode.CMYK, "CMYK")
        self.assertEqual(mode.CMYK64, "CMYK64")


if __name__ == "__main__":
    testing.main()
