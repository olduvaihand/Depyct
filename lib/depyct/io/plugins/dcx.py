# depyct/io/plugins/dcx.py

from depyct.io.format import FormatBase


class DCXFormat(FormatBase):
    """File format plugin for DCX images
    =================================

    """

    extensions = ("dcx",)
    mimetypes = ("image/x-dcx",)

    def read(self, image_cls, fp, **options):
        raise NotImplementedError

    def write(self, image, fp, **options):
        raise NotImplementedError
