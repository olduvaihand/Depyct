# depyct/io/plugins/png.py

from depyct.io.format import FormatBase


class PNGFormat(FormatBase):
    """File format plugin for PNG images
    =================================

    """

    extensions = ("png",)
    mimetypes = ("image/png",)

    def read(self):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def write(self):
        raise NotImplementedError
