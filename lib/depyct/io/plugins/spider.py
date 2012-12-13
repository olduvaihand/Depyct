# depyct/io/plugins/spider.py

from depyct.io.format import FormatBase


class SpiderFormat(FormatBase):
    """File format plugin for Spider 2D images
    ==========================================

    """

    extensions = ("spi",)
    mimetypes = ()

    def open(self, image_cls, filename, **options):
        raise NotImplementedError

    def save(self, image, filename, **options):
        raise NotImplementedError
