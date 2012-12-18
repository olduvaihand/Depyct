# depyct/io/plugins/xpm.py

from depyct.io.format import FormatBase


class XPMFormat(FormatBase):
    """File format plugin for XPM images
    =================================

    """

    extensions = ("xpm", "pm")
    mimetypes = ("image/x-xpm", "image/x-xpixelmap")

    def read(self):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def write(self):
        raise NotImplementedError
