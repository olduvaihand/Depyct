# depyct/io/plugins/jng.py

from depyct.io.format import FormatBase


class JNGFormat(FormatBase):
    """File format plugin for JNG images
    =================================

    """

    extensions = ("jng",)
    mimetypes = ("image/x-jng",)

    def open(self, image_cls, filename, **options):
        raise NotImplementedError

    def save(self, image, filename, **options):
        raise NotImplementedError
