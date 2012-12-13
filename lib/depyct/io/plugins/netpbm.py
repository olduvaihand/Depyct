# depyct/io/plugins/netpbm.py

from depyct.io.format import FormatBase


class NetpbmFormat(FormatBase):
    """Base file format plugin for Netpbm images
    ============================================

    """

    extensions = ()
    mimetypes = ()

    def open(self, image_cls, filename, **options):
        raise NotImplementedError

    def save(self, image, filename, **options):
        raise NotImplementedError


class PBMFormat(NetpbmFormat):
    """Plugin for PBM images
    ========================

    """

    extensions = ("pbm",)
    mimetypes = ("image/x-portable-bitmap",)

    def open(self, image_cls, filename, **options):
        raise NotImplementedError

    def save(self, image, filename, **options):
        raise NotImplementedError


class PGMFormat(NetpbmFormat):
    """Plugin for PGM images
    ========================

    """

    extensions = ("pgm",)
    mimetypes = ("image/x-portable-graymap",)

    def open(self, image_cls, filename, **options):
        raise NotImplementedError

    def save(self, image, filename, **options):
        raise NotImplementedError


class PPMFormat(NetpbmFormat):
    """Plugin for PPM images
    ========================

    """

    extensions = ("ppm",)
    mimetypes = ("image/x-portable-pixmap",)

    def open(self, image_cls, filename, **options):
        raise NotImplementedError

    def save(self, image, filename, **options):
        raise NotImplementedError


class PNMFormat(NetpbmFormat):
    """Plugin for PNM images
    ========================

    """

    extensions = ("pnm",)
    mimetypes = ("image/x-portable-anymap",)

    def open(self, image_cls, filename, **options):
        # figure out which format and dispatch to it
        raise NotImplementedError

    def save(self, image, filename, **options):
        # figure out which format and dispatch to it
        raise NotImplementedError


class PAMFormat(NetpbmFormat):
    """Plugin for PAM images
    ========================

    """

    extensions = ("pam",)
    mimetypes = ("image/x-portable-anymap",)
