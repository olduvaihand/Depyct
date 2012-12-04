# test/unit_tests/test_image/test_image_mode.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
from depyct.testing import DepyctUnitTest
from depyct.image.mode import (ImageMode, MODES, L,
    L16, L32, LA, LA32, #L16F,
    L32F, L64F, LA32F, RGB, RGB48, RGBA, RGBA64,
    #RGB48F, RGBA64F,
    RGB96F, RGBA128F, RGB192F, RGBA256F, YV12, JPEG_YV12,
    #HSV, HSL,
    HSV96, HSL96, HSV192, HSL192, CMYK, CMYK64
)


class ImageModeTest(DepyctUnitTest):

    @classmethod
    def setUpClass(cls):
        cls.bytes_per_pixel = {
                L: 1,
                L16: 2,
                L32: 4,
                LA: 2,
                LA32: 4,
                #L16F: 2,
                L32F: 4,
                L64F: 8,
                LA32F: 8,
                RGB: 3,
                RGB48: 6,
                RGBA: 4,
                RGBA64: 8,
                #RGB48F: 6,
                #RGBA64F: 8,
                RGB96F: 12,
                RGBA128F: 16,
                RGB192F: 24,
                RGBA256F: 32,
                #HSV: 6,
                #HSL: 6,
                HSV96: 12,
                HSL96: 12,
                HSV192: 24,
                HSL192: 24,
                CMYK: 4,
                CMYK64: 8,
            }

    def test_is_float(self):
        float_modes = (#L16F,
                       L32F, L64F, LA32F, 
                       #RGB48F, RGBA64F, 
                       RGB96F, RGBA128F, RGB192F, RGBA256F,
                       HSV96, HSL96, HSV192, HSL192)
        for mode in float_modes:
            self.assertTrue(mode._is_float)
        for mode in MODES:
            if mode not in float_modes:
                self.assertFalse(mode._is_float)

    def test_bytes_per_pixel(self):
        for mode, bytes_per_pixel in self.bytes_per_pixel.items():
            self.assertEquals(mode.bytes_per_pixel, bytes_per_pixel)

        with self.assertRaises(TypeError):
            YV12.bytes_per_pixel
        with self.assertRaises(TypeError):
            JPEG_YV12.bytes_per_pixel

    def test_get_length(self):
        for mode, bytes_per_pixel in self.bytes_per_pixel.items():
            self.assertEquals(mode.get_length((10, 10)), 100*bytes_per_pixel)

        self.assertEquals(YV12.get_length((10, 10)), 150)
        self.assertEquals(JPEG_YV12.get_length((10, 10)), 150)

    def test_string_equality(self):
        self.assertEquals(L16, "L16")
        self.assertEquals(L32, "I")
        self.assertEquals(LA, "LA")
        self.assertEquals(LA32, "LA32")
        #self.assertEquals(L16F, "L16F")
        self.assertEquals(L32F, "L32F")
        self.assertEquals(L64F, "L64F")
        self.assertEquals(LA32F, "LA32F")
        self.assertEquals(RGB, "RGB")
        self.assertEquals(RGB48, "RGB48")
        self.assertEquals(RGBA, "RGBA")
        self.assertEquals(RGBA64, "RGBA64")
        #self.assertEquals(RGB48F, "RGB48F")
        #self.assertEquals(RGBA64F, "RGBA64F")
        self.assertEquals(RGB96F, "RGB96F")
        self.assertEquals(RGBA128F, "RGBA128F")
        self.assertEquals(RGB192F, "RGB192F")
        self.assertEquals(RGBA256F, "RGBA256F")
        self.assertEquals(YV12, "YV12")
        self.assertEquals(JPEG_YV12, "JPEG_YV12")
        #self.assertEquals(HSV, "HSV")
        #self.assertEquals(HSL, "HSL")
        self.assertEquals(HSV96, "HSV96")
        self.assertEquals(HSL96, "HSL96")
        self.assertEquals(HSV192, "HSV192")
        self.assertEquals(HSL192, "HSL192")
        self.assertEquals(CMYK, "CMYK")
        self.assertEquals(CMYK64, "CMYK64")
