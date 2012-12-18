# depyct/io/plugins/pix.py

from depyct.io.format import FormatBase


class PIXFormat(FormatBase):
    """File format plugin for PIX images
    =================================

    """

    extensions = ("pix", "matte", "mask", "alpha", "als")
    mimetypes = ()

    def read(self):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def write(self):
        raise NotImplementedError
