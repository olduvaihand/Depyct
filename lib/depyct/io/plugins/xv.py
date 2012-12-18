# depyct/io/plugins/xv.py

from depyct.io.format import FormatBase


class XVFormat(FormatBase):
    """File format plugin for XV Thumbnail images
    =============================================

    """

    extensions = ("xv",)
    mimetypes = ()

    def read(self, image_cls, fp, **options):
        raise NotImplementedError

    def write(self, image, fp, **options):
        raise NotImplementedError
