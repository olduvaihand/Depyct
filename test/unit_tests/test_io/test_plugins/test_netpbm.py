# test/unit_tests/test_io/test_plugins/test_netbpm.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
import io

from depyct import testing
from depyct import image
from depyct.image import mode
from depyct.io.plugins import netpbm


class PBMFormatTest(testing.DepyctUnitTest):

    _IMAGE = (
        (255, 255,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0),
        (255,   0, 255,   0,   0, 255,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 255,   0),
        (255,   0, 255,   0, 255, 255, 255,   0, 255, 255, 255,   0, 255,   0, 255,   0, 255, 255, 255,   0, 255, 255, 255),
        (255,   0, 255,   0, 255,   0,   0,   0, 255,   0, 255,   0,   0, 255, 255,   0, 255,   0,   0,   0,   0, 255,   0),
        (255, 255,   0,   0,   0, 255,   0,   0, 255, 255, 255,   0,   0,   0, 255,   0, 255, 255, 255,   0,   0,   0, 255),
        (  0,   0,   0,   0,   0,   0,   0,   0, 255,   0,   0,   0, 255,   0, 255,   0,   0,   0,   0,   0,   0,   0,   0),
        (  0,   0,   0,   0,   0,   0,   0,   0, 255,   0,   0,   0,   0, 255,   0,   0,   0,   0,   0,   0,   0,   0,   0),
    )

    def setUp(self):
        self.test_im = image.Image(mode.L, image.ImageSize(23, 7))
        self.test_im[:] = self._IMAGE

    def test_read_plain(self):
        pbm_format = netpbm.PBMFormat(image.Image, **{"format": "plain"})
        im = pbm_format.open(self.get_data_path("depyct-plain.pbm"))
        self.assertEqual(im, self.test_im)

    def test_write_plain(self):
        pbm_format = netpbm.PBMFormat(image.Image, **{"format": "plain"})
        capture = io.BytesIO()
        pbm_format.save(self.test_im, capture)
        expected = self.read_data("depyct-plain.pbm")
        self.assertEqual(capture.getvalue(), expected)
        capture.close()

    def test_read_raw(self):
        pbm_format = netpbm.PBMFormat(image.Image)
        im = pbm_format.open(self.get_data_path("depyct-raw.pbm"))
        self.assertEqual(im, self.test_im)

    def test_write_raw(self):
        pbm_format = netpbm.PBMFormat(image.Image)
        capture = io.BytesIO()
        pbm_format.save(self.test_im, capture)
        expected = self.read_data("depyct-raw.pbm")
        self.assertEqual(capture.getvalue(), expected)
        capture.close()


class PGMFormatTest(testing.DepyctUnitTest):
    pass


class PPMFormatTest(testing.DepyctUnitTest):
    pass


class PNMFormatTest(testing.DepyctUnitTest):
    pass


class PAMFormatTest(testing.DepyctUnitTest):
    pass


if __name__ == "__main__":
    testing.main()
