# depyct/io/plugins/png.py

from depyct.io.format import FormatBase


class PNGFormat(FormatBase):
    """File format plugin for PNG images
    =================================

    """

    extensions = ("png",)
    mimetypes = ("image/png",)

    def open(self, image_cls, filename, **options):
        raise NotImplementedError

    def save(self, image, filename, **options):
        raise NotImplementedError
