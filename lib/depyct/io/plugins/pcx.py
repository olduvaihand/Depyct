# depyct/io/plugins/pcx.py

from depyct.io.format import FormatBase


class PCXFormat(FormatBase):
    """File format plugin for PCX images
    =================================

    """

    extensions = ("pcx",)
    mimetypes = ("image/x-pcx",)

    def open(self, image_cls, filename, **options):
        raise NotImplementedError

    def save(self, image, filename, **options):
        raise NotImplementedError
