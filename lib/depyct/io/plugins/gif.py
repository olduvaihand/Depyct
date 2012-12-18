# depyct/io/plugins/gif.py

from depyct.io.format import FormatBase


class GIFFormat(FormatBase):
    """File format plugin for GIF images
    =================================

    """

    extensions = ("gif", "gfa", "giff")
    mimetypes = ("image/gif",)

    def read(self, image_cls, fp, **options):
        raise NotImplementedError

    def write(self, image, fp, **options):
        raise NotImplementedError
