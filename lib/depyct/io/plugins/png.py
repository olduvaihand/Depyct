# depyct/io/plugins/png.py

from depyct.io.format import FormatBase


class PNGFormat(FormatBase):
    """File format plugin for PNG images
    =================================

    """

    extensions = ("png",)
    mimetypes = ("image/png",)

    def read(self, image_cls, fp, **options):
        raise NotImplementedError

    def write(self, image, fp, **options):
        raise NotImplementedError
