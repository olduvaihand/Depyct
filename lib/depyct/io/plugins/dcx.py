# depyct/io/plugins/dcx.py

from depyct.io.format import FormatBase


class DCXFormat(FormatBase):
    """File format plugin for DCX images
    =================================

    """

    extensions = ("dcx",)
    mimetypes = ("image/x-dcx",)

    def read(self):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def write(self):
        raise NotImplementedError
