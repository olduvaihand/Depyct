# depyct/io/plugins/jpeg.py

from depyct.io.format import FormatBase


class JPEGFormat(FormatBase):
    """File format plugin for XPM images
    =================================

    """

    extensions = ("jpg", "jpeg", "jpe", "jif", "jfif", "jfi")
    mimetypes = ("image/jpeg",)

    def read(self):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def write(self):
        raise NotImplementedError
