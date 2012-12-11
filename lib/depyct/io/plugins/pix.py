# depyct/io/plugins/pix.py

from depyct.io.format import FormatBase


class PIXFormat(FormatBase):
    """File format plugin for PIX images
    =================================

    """

    extensions = ("pix", "matte", "mask", "alpha", "als")
    mimetypes = ()

    def open(self, image_cls, filename, **options):
        raise NotImplementedError

    def save(self, image, filename, **options):
        raise NotImplementedError
