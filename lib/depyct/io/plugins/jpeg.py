# depyct/io/plugins/jpeg.py

from depyct.io.format import FormatBase


class JPEGFormat(FormatBase):
    """File format plugin for XPM images
    =================================

    """

    extensions = ("jpg", "jpeg", "jpe", "jif", "jfif", "jfi")
    mimetypes = ("image/jpeg",)

    def open(self, image_cls, filename, **options):
        raise NotImplementedError

    def save(self, image, filename, **options):
        raise NotImplementedError
