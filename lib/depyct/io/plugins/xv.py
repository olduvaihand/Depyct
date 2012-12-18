# depyct/io/plugins/xv.py

from depyct.io.format import FormatBase


class XVFormat(FormatBase):
    """File format plugin for XV Thumbnail images
    =============================================

    """

    extensions = ("xv",)
    mimetypes = ()

    def read(self):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def write(self):
        raise NotImplementedError
