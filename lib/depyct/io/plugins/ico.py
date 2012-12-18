# depyct/io/plugins/ico.py

from depyct.io.format import FormatBase


class ICOCURFormat(FormatBase):
    """File format plugin for ICO/CUR images
    ========================================

    """

    extensions = ("ico", "cur")
    mimetypes = ("image/vnd.microsoft.icon", "image/x-icon")

    def read(self):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def write(self):
        raise NotImplementedError
