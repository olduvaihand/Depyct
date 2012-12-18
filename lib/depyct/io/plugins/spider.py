# depyct/io/plugins/spider.py

from depyct.io.format import FormatBase


class SpiderFormat(FormatBase):
    """File format plugin for Spider 2D images
    ==========================================

    """

    extensions = ("spi",)
    mimetypes = ()

    def read(self, image_cls, fp, **options):
        raise NotImplementedError

    def write(self, image, fp, **options):
        raise NotImplementedError
