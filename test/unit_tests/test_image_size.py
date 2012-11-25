# test/unit_tests/test_image_size.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
from depyct.testing import DepyctUnitTest
from depyct.image import ImageSize


class ImageSizeTest(DepyctUnitTest):

    def test___repr__(self):
        im_size = ImageSize(10, 10)
        self.assertEquals(repr(im_size), "ImageSize(width=10, height=10)")

    def test_bad_input(self):
        for w, h in ((0, 10), (-1, 10), (0, 0), (-1, -1), (10, 0), (10, -1)):
            with self.assertRaises(ValueError):
                ImageSize(w, h)

        for w, h in ((1., 1), (1, 1.), (1., 1.), ('a', 1), (1, 'a'), 'aa'):
            with self.assertRaises(TypeError):
                ImageSize(w, h)

