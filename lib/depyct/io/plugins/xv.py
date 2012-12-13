# depyct/io/plugins/xv.py

from depyct.io.format import FormatBase


class XVFormat(FormatBase):
    """File format plugin for XV Thumbnail images
    =============================================

    """

    extensions = ("xv",)
    mimetypes = ()

    def open(self, image_cls, filename, **options):
        raise NotImplementedError

    def save(self, image, filename, **options):
        raise NotImplementedError
