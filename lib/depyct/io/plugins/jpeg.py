# depyct/io/plugins/jpeg.py

from depyct.io.format import FormatBase


class JPEGFormat(FormatBase):
    """File format plugin for XPM images
    =================================

    """

    extensions = ("jpg", "jpeg", "jpe", "jif", "jfif", "jfi")
    mimetypes = ("image/jpeg",)

    def read(self, image_cls, fp, **options):
        raise NotImplementedError

    def write(self, image, fp, **options):
        raise NotImplementedError
