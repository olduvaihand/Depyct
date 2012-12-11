# depyct/io/plugins/dcx.py

from depyct.io.format import FormatBase


class DCXFormat(FormatBase):
    """File format plugin for DCX images
    =================================

    """

    extensions = ("dcx",)
    mimetypes = ("image/x-dcx",)

    def open(self, image_cls, filename, **options):
        raise NotImplementedError

    def save(self, image, filename, **options):
        raise NotImplementedError
