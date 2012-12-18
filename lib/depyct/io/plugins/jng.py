# depyct/io/plugins/jng.py

from depyct.io.format import FormatBase


class JNGFormat(FormatBase):
    """File format plugin for JNG images
    =================================

    """

    extensions = ("jng",)
    mimetypes = ("image/x-jng",)

    def read(self, image_cls, fp, **options):
        raise NotImplementedError

    def write(self, image, fp, **options):
        raise NotImplementedError
