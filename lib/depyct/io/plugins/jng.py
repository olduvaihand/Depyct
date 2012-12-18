# depyct/io/plugins/jng.py

from depyct.io.format import FormatBase


class JNGFormat(FormatBase):
    """File format plugin for JNG images
    =================================

    """

    extensions = ("jng",)
    mimetypes = ("image/x-jng",)

    def read(self):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def write(self):
        raise NotImplementedError
