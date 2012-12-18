# depyct/io/plugins/pcx.py

from depyct.io.format import FormatBase


class PCXFormat(FormatBase):
    """File format plugin for PCX images
    =================================

    """

    extensions = ("pcx",)
    mimetypes = ("image/x-pcx",)

    def read(self):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def write(self):
        raise NotImplementedError
