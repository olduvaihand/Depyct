# depyct/io/plugins/ico.py

from depyct.io.format import FormatBase


class ICOCURFormat(FormatBase):
    """File format plugin for ICO/CUR images
    ========================================

    """

    extensions = ("ico", "cur")
    mimetypes = ("image/vnd.microsoft.icon",)

    def open(self, image_cls, filename, **options):
        raise NotImplementedError

    def save(self, image, filename, **options):
        raise NotImplementedError
