# depyct/io/plugins/xpm.py

from depyct.io.format import FormatBase


class XPMFormat(FormatBase):
    """File format plugin for XPM images
    =================================

    """

    extensions = ("xpm",)
    mimetypes = ("image/x-xpm", "image/x-xpixelmap")

    def open(self, image_cls, filename, **options):
        raise NotImplementedError

    def save(self, image, filename, **options):
        raise NotImplementedError
