# depyct/io/plugins/gif.py

from depyct.io.format import FormatBase


class GIFFormat(FormatBase):
    """File format plugin for GIF images
    =================================

    """

    extensions = ("gif",)
    mimetypes = ("image/gif",)

    def open(self, image_cls, filename, **options):
        raise NotImplementedError

    def save(self, image, filename, **options):
        raise NotImplementedError
