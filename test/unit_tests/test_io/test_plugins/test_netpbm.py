# test/unit_tests/test_io/test_plugins/test_netbpm.py
# Copyright (c) 2012-2017 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
import io
import os

from depyct import testing
from depyct import image as image_lib
from depyct.image import mode
from depyct.io.plugins import netpbm


class NetpbmTest(testing.DepyctUnitTest):

    FORMAT_CLS = None

    def check_read_plain(self, path, expected):
        options = {"format": "plain"}
        self.check_read(options, path, expected)

    def check_read_raw(self, path, expected):
        options = {"format": "raw"}
        self.check_read(options, path, expected)

    def check_read(self, options, path, expected):
        fmt = self.FORMAT_CLS(image_lib.Image, **options)
        im = fmt.open(self.get_data_path(path))
        self.assertEqual(im, expected)

    def check_write_plain(self, image, expected_path, **overrides):
        options = {"format": "plain"}
        options.update(overrides)
        self.check_write(options, image, expected_path)

    def check_write_raw(self, image, expected_path, **overrides):
        options = {"format": "raw"}
        options.update(overrides)
        self.check_write(options, image, expected_path)

    def check_write(self, options, image, expected_path):
        fmt = self.FORMAT_CLS(image_lib.Image, **options)
        capture = io.BytesIO()
        fmt.save(image, capture)
        expected = self.read_data(expected_path)
        self.assertEqual(capture.getvalue(), expected)
        capture.close()

    def get_data_path(self, path):
        rerooted_path = os.path.join('netpbm', path)
        return super(NetpbmTest, self).get_data_path(rerooted_path)


class PBMFormatTest(NetpbmTest):

    FORMAT_CLS = netpbm.PbmFormat

    B, _ = 255, 0

    IMAGE = (
        (B, B, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _),
        (B, _, B, _, _, B, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, B, _),
        (B, _, B, _, B, B, B, _, B, B, B, _, B, _, B, _, B, B, B, _, B, B, B),
        (B, _, B, _, B, _, _, _, B, _, B, _, _, B, B, _, B, _, _, _, _, B, _),
        (B, B, _, _, _, B, _, _, B, B, B, _, _, _, B, _, B, B, B, _, _, _, B),
        (_, _, _, _, _, _, _, _, B, _, _, _, B, _, B, _, _, _, _, _, _, _, _),
        (_, _, _, _, _, _, _, _, B, _, _, _, _, B, _, _, _, _, _, _, _, _, _),
    )

    @classmethod
    def get_test_image(cls):
        im = image_lib.Image(mode.L, image_lib.ImageSize(23, 7))
        im[:] = cls.IMAGE
        return im

    def setUp(self):
        self.test_im = self.get_test_image()

    def test_read_plain(self):
        self.check_read_plain("in.plain.pbm", self.test_im)

    def test_write_plain(self):
        self.check_write_plain(self.test_im, "out.plain.pbm")

    def test_read_raw(self):
        self.check_read_raw("in.raw.pbm", self.test_im)

    def test_write_raw(self):
        self.check_write_raw(self.test_im, "out.raw.pbm")


class PGMFormatTest(NetpbmTest):

    FORMAT_CLS = netpbm.PgmFormat

    B, G, _ = 255, 119, 0

    IMAGE = (
        (B, B, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _),
        (B, _, B, _, _, B, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, B, _),
        (B, _, B, _, B, B, B, _, B, B, B, _, B, _, B, _, B, B, B, _, B, B, B),
        (B, _, B, _, B, _, _, _, B, _, B, _, _, B, B, _, B, _, _, _, _, B, _),
        (B, B, _, _, _, B, _, _, B, B, B, _, _, _, B, _, B, B, B, _, _, _, B),
        (G, G, G, G, G, G, G, G, B, G, G, G, B, G, B, G, G, G, G, G, G, G, G),
        (_, _, _, _, _, _, _, _, B, _, _, _, _, B, _, _, _, _, _, _, _, _, _),
    )

    @classmethod
    def get_test_image(cls):
        im = image_lib.Image(mode.L, image_lib.ImageSize(23, 7))
        im[:] = cls.IMAGE
        return im

    def setUp(self):
        self.test_im = self.get_test_image()

    def test_read_plain(self):
        self.check_read_plain("in.plain.pgm", self.test_im)

    def test_write_plain(self):
        self.check_write_plain(self.test_im, "out.plain.pgm", maxval=15)

    def test_read_raw(self):
        self.check_read_raw("in.raw.pgm", self.test_im)

    def test_write_raw(self):
        self.check_write_raw(self.test_im, "out.raw.pgm", maxval=15)


class PPMFormatTest(NetpbmTest):

    FORMAT_CLS = netpbm.PpmFormat

    R = (255, 0, 0)
    O = (255, 119, 0)
    Y = (255, 255, 0)
    G = (0, 255, 0)
    B = (0, 0, 255)
    V = (255, 0, 255)
    w = (255, 255, 255)
    _ = (0, 0, 0)

    IMAGE = (
        (R, R, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _),
        (R, _, R, _, _, O, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, V, _),
        (R, _, R, _, O, O, O, _, Y, Y, Y, _, G, _, G, _, B, B, B, _, V, V, V),
        (R, _, R, _, O, _, _, _, Y, _, Y, _, _, G, G, _, B, _, _, _, _, V, _),
        (R, R, _, _, _, O, _, _, Y, Y, Y, _, _, _, G, _, B, B, B, _, _, _, V),
        (w, w, w, w, w, w, w, w, Y, w, w, w, G, w, G, w, w, w, w, w, w, w, w),
        (_, _, _, _, _, _, _, _, Y, _, _, _, _, G, _, _, _, _, _, _, _, _, _),
    )

    @classmethod
    def get_test_image(cls):
        im = image_lib.Image(mode.RGB, image_lib.ImageSize(23, 7))
        im[:] = cls.IMAGE
        return im

    def setUp(self):
        self.test_im = self.get_test_image()

    def test_read_plain(self):
        self.check_read_plain("in.plain.ppm", self.test_im)

    def test_write_plain(self):
        self.check_write_plain(self.test_im, "out.plain.ppm", maxval=15)

    def test_read_raw(self):
        self.check_read_raw("in.raw.ppm", self.test_im)

    def test_write_raw(self):
        self.check_write_raw(self.test_im, "out.raw.ppm", maxval=15)


class PNMFormatTest(NetpbmTest):

    FORMAT_CLS = netpbm.PnmFormat

    # PBM

    def test_read_plain_pbm(self):
        test_im = PBMFormatTest.get_test_image()
        self.check_read_plain("in.plain-pbm.pnm", test_im)

    def test_write_plain_pbm(self):
        test_im = PBMFormatTest.get_test_image()
        self.check_write_plain(test_im, "out.plain-pbm.pnm")

    def test_read_raw_pbm(self):
        test_im = PBMFormatTest.get_test_image()
        self.check_read_raw("in.raw-pbm.pnm", test_im)

    def test_write_raw_pbm(self):
        test_im = PBMFormatTest.get_test_image()
        self.check_write_raw(test_im, "out.raw-pbm.pnm")

    # PGM

    def test_read_plain_pgm(self):
        test_im = PGMFormatTest.get_test_image()
        self.check_read_plain("in.plain-pgm.pnm", test_im)

    def test_write_plain_pgm(self):
        test_im = PGMFormatTest.get_test_image()
        self.check_write_plain(test_im, "out.plain-pgm.pnm", maxval=15)

    def test_read_raw_pgm(self):
        test_im = PGMFormatTest.get_test_image()
        self.check_read_raw("in.raw-pgm.pnm", test_im)

    def test_write_raw_pgm(self):
        test_im = PGMFormatTest.get_test_image()
        self.check_write_raw(test_im, "out.raw-pgm.pnm", maxval=15)

    # PPM

    def test_read_plain_ppm(self):
        test_im = PPMFormatTest.get_test_image()
        self.check_read_plain("in.plain-ppm.pnm", test_im)

    def test_write_plain_ppm(self):
        test_im = PPMFormatTest.get_test_image()
        self.check_write_plain(test_im, "out.plain-ppm.pnm", maxval=15)

    def test_read_raw_ppm(self):
        test_im = PPMFormatTest.get_test_image()
        self.check_read_raw("in.raw-ppm.pnm", test_im)

    def test_write_raw_ppm(self):
        test_im = PPMFormatTest.get_test_image()
        self.check_write_raw(test_im, "out.raw-ppm.pnm", maxval=15)


class PAMFormatTest(testing.DepyctUnitTest):
    pass


if __name__ == "__main__":
    testing.main()
