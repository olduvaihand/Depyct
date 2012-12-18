# depyct/io/plugins/netpbm.py
from itertools import chain
import re
import struct

from depyct.io.format import FormatBase, registry
from depyct.image.mode import L, L16, RGB, RGB48
from depyct import util


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


_netpbm_header = (br"^(?P<magic_number>P[{}])\n\s*"
                  br"(?:(?:#.*?)\n\s*)??"
                  br"(?P<width>\d+)\s+"
                  br"(?:(?:#.*?)\n\s*)??"
                  br"(?P<height>\d+)\s+")
_netpbm_maxval = br"(?:(?:#.*?)\n\s*)??(?P<maxval>\d+)\s+(?:(?:#.*?)\n\s*)??"

PBM_HEADER_RE = re.compile(_netpbm_header.format(br"14"))
PGM_HEADER_RE = re.compile(_netpbm_header.format(br"25") + _netpbm_maxval)
PPM_HEADER_RE = re.compile(_netpbm_header.format(br"36") + _netpbm_maxval)


class PBMFormat(NetpbmFormat):
    """Plugin for PBM images
    ========================

    """

    extensions = ("pbm",)
    mimetypes = ("image/x-portable-bitmap",)

    def open(self, image_cls, filename, **options):
        with open(filename, "rb") as fp:
            m = PBM_HEADER_RE.match(fp.read(512))
            if m is None:
                raise IOError("{} does not appear to be a valid PBM "
                              "file".format(filename))
            magic_number = m.group("magic_number")
            width, height = int(m.group("width")), int(m.group("height"))
            im = image_cls(L, size=(width, height))
            fp.seek(m.end())
            try:
                data = {b"P1": self._open_plain,
                        b"P4": self._open_raw}[magic_number](fp, width, height)
            except AssertionError as err:
                raise IOError(err.message)
            im[:] = data
            return im

    def _open_plain(self, fp, width, height):
        data = []
        for i, line in enumerate(fp):
            assert re.match("^(?:([ \t10]+)+)$", line), (
                   "There should be no characters other than `1`, `0`, "
                   "` `, and `\t` on a given scan line in pbm raster data. "
                   "Check line {} of input.".format(i))
            line_data = [(255 if b == "1" else 0,) for b in line.split()]
            assert len(line_data) == width, (
                   "Incorrect amount of pixel data read.  Got {} pixels on "
                   "line {}, expected {}.".format(len(line_data), i, width))
            data.append(line_data)
        assert len(data) == height, (
               "Incorrect number of lines read.  Got {}, expected "
               "{}.".format(len(data), height))
        return data

    def _open_raw(self, fp, width, height):
        # FIXME: this can clearly be done more efficiently.  I'm just trying
        #        to get some consistent approaches before revising the io
        #        system to accomodate stream handling, etc
        data = []
        chunksize, remainder = divmod(width, 8)
        if remainder:
            chunksize += 1

        # TODO: move this to something external
        if util.py27:
            unpack = lambda chunk: [(255 if (b>>i) & 1 else 0,)
                                    for b in map(ord, chunk)
                                    for i in range(7,-1,-1)]
        else:
            unpack = lambda chunk: [(255 if (b>>i) & 1 else 0,) for b in chunk
                                    for i in range(7,-1,-1)]

        while True:
            chunk = fp.read(chunksize)
            if not chunk:
                break
            chunk_data = unpack(chunk)[:width]
            data.append(chunk_data)
        return data

    def save(self, image, filename, **options):
        clip = options.get("clip", lambda c: c != image.mode.transparent_color)
        format = options.get("format", "raw")
        magic_number = "P1" if format == "plain" else "P4"
        with open(filename, "wb") as fp:
            fp.write(b"P{}\n{} {}\n".format(magic_number, *image.size))
            if format == "plain":
                self._save_plain(fp, image, clip)
            else:
                self._save_raw(fp, image, clip)

    def _save_plain(self, fp, image, clip):
        for i, line in enumerate(image, 1):
            fp.write(b" ".join(str(int(clip(p.value))) for p in line))
            if i != image.size.height:
                fp.write(b"\n")

    def _save_raw(self, fp, image, clip):
        nbytes, remainder = divmod(image.size.width, 8)
        if remainder:
            nbytes += 1
        for line in image:
            bytes = list(util.pack_bits(clip(p.value) for p in line))
            fp.write(struct.pack(">{}B".format(nbytes), *bytes))


class PGMFormat(NetpbmFormat):
    """Plugin for PGM images
    ========================

    """

    extensions = ("pgm",)
    mimetypes = ("image/x-portable-graymap",)

    def open(self, image_cls, filename, **options):
        with open(filename, "rb") as fp:
            m = PGM_HEADER_RE.match(fp.read(512))
            if m is None:
                raise IOError("{} does not appear to be a valid PGM "
                              "file".format(filename))
            magic_number = m.group("magic_number")
            width, height = int(m.group("width")), int(m.group("height"))
            maxval = int(m.group("maxval"))
            mode = L if maxval <= 255 else L16
            bit_depth = mode.bits_per_component
            scale = lambda i: (int(float(i) * ((2**bit_depth) - 1) / maxval),)
            im = image_cls(mode, size=(width, height))
            fp.seek(m.end())
            try:
                data = {b"P2": self._open_plain,
                        b"P5": self._open_raw}[magic_number](
                                fp, scale, mode.bytes_per_pixel, width, height)
            except AssertionError as err:
                raise IOError(err.message)
            im[:] = data
            return im

    def _open_plain(self, fp, scale, bpp, width, height):
        data = []
        for line in fp:
            line_data = [scale(int(i)) for i in line.split()]
            data.append(line_data)
        return data

    def _open_raw(self, fp, scale, bpp, width, height):
        data = []
        struct_format = ">{}{}".format(width, "B" if bpp == 1 else "H")
        chunksize = width * bpp
        while True:
            chunk = fp.read(chunksize)
            if not chunk:
                break
            line_data = [scale(p) for p in struct.unpack(struct_format, chunk)]
            data.append(line_data)
        return data

    def save(self, image, filename, **options):
        if image.components != 1:
            # issue a warning about loss of information
            pass
        format = options.get("format", "raw")
        assert format in ("raw", "plain")
        max_in = 2**image.mode.bits_per_component-1
        maxval = options.get("maxval", max_in)
        assert 0 < maxval < 65536
        magic_number = "P2" if format == "plain" else "P5"
        width, height = image.size
        # TODO: have a different scaling function available for different modes
        scale = lambda i: int(float(i[0]) * maxval / max_in)
        with open(filename, "wb") as fp:
            fp.write("{}\n{} {}\n{}\n".format(magic_number, width, height,
                                              maxval))
            if format == "plain":
                self._save_plain(image, fp, maxval, scale)
            else:
                self._save_raw(image, fp, maxval, scale)

    def _save_plain(self, image, fp, maxval, scale):
        for i, line in enumerate(image):
            fp.write(b" ".join(str(scale(p)) for p in line))
            if i != image.size.height:
                fp.write(b"\n")

    def _save_raw(self, image, fp, maxval, scale):
        struct_format = ">{}{}".format(image.size.width,
                                       "B" if maxval <= 255 else "H")
        for i, line in enumerate(image):
            fp.write(struct.pack(struct_format, *(scale(p) for p in line)))
        

def group(iterable, chunksize):
    from itertools import izip
    args = [iter(iterable)] * chunksize
    return izip(*args)


class PPMFormat(NetpbmFormat):
    """Plugin for PPM images
    ========================

    """

    extensions = ("ppm",)
    mimetypes = ("image/x-portable-pixmap",)

    def open(self, image_cls, filename, **options):
        with open(filename, "rb") as fp:
            m = PPM_HEADER_RE.match(fp.read(512))
            if m is None:
                raise IOError("{} does not appear to be a valid PPM "
                              "file".format(filename))
            magic_number = m.group("magic_number")
            width, height = int(m.group("width")), int(m.group("height"))
            maxval = int(m.group("maxval"))
            mode = RGB if maxval <= 255 else RGB48
            bit_depth = mode.bits_per_component
            _scale = lambda i: int(float(i) * ((2**bit_depth) - 1) / maxval)
            scale = lambda p: tuple(map(_scale, p))
            im = image_cls(mode, size=(width, height))
            fp.seek(m.end())
            try:
                data = {b"P3": self._open_plain,
                        b"P6": self._open_raw}[magic_number](
                                fp, scale, bit_depth//8, width, height)
            except AssertionError as err:
                raise IOError(err.message)
            im[:] = data
            return im

    def _open_plain(self, fp, scale, bpp, width, height):
        data = []
        for line in fp:
            pixels = group(line.split(), 3)
            line_data = [scale(map(int, p)) for p in pixels]
            data.append(line_data)
        return data

    def _open_raw(self, fp, scale, bpp, width, height):
        data = []
        struct_format = ">{}{}".format(width*3, "B" if bpp == 1 else "H")
        chunksize = width * 3 * bpp
        while True:
            chunk = fp.read(chunksize)
            if not chunk:
                break
            pixels = group(struct.unpack(struct_format, chunk), 3)
            line_data = [scale(p) for p in pixels]
            data.append(line_data)
        return data

    def save(self, image, filename, **options):
        if image.components != 1:
            # issue a warning about loss of information
            pass
        format = options.get("format", "raw")
        assert format in ("raw", "plain")
        max_in = 2**image.mode.bits_per_component-1
        maxval = options.get("maxval", max_in)
        assert 0 < maxval < 65536
        magic_number = "P3" if format == "plain" else "P6"
        width, height = image.size
        # TODO: have a different scaling function available for different modes
        _scale = lambda i: int(float(i) * maxval / max_in)
        scale = lambda p: tuple(map(_scale, p))
        with open(filename, "wb") as fp:
            fp.write("{}\n{} {}\n{}\n".format(magic_number, width, height,
                                              maxval))
            if format == "plain":
                self._save_plain(image, fp, maxval, scale)
            else:
                self._save_raw(image, fp, maxval, scale)

    def _save_plain(self, image, fp, maxval, scale):
        for i, line in enumerate(image):
            fp.write(b"\t".join(b" ".join(map(str, scale(p))) for p in line))
            if i != image.size.height:
                fp.write(b"\n")

    def _save_raw(self, image, fp, maxval, scale):
        struct_format = ">{}{}".format(image.size.width * 3,
                                       "B" if maxval <= 255 else "H")
        for i, line in enumerate(image):
            data = []
            for p in line:
                data.extend(scale(p))
            fp.write(struct.pack(struct_format, *data))


class PNMFormat(NetpbmFormat):
    """Plugin for PNM images
    ========================

    """

    extensions = ("pnm",)
    mimetypes = ("image/x-portable-anymap",)

    def open(self, image_cls, filename, **options):
        with open(filename, "rb") as fp:
            magic_number = fp.read(2)
        try:
            ext = {"P1": "pbm", "P4": "pbm",
                   "P2": "pgm", "P5": "pgm",
                   "P3": "ppm", "P6": "ppm"}[magic_number]
        except KeyError:
            raise IOError("Unrecognized magic number {} for pnm format. "
                          "Should be P1, P2, or P3 for plain text pbm, "
                          "pgm, or ppm, respectively, or P4, P5, or P6 for "
                          "raw pbm, pgm, or ppm, respectively.".format(
                              magic_number))
        format = registry[ext](**self.config)
        return format.open(image_cls, filename, **options)

    def save(self, image, filename, **options):
        # figure out which format and dispatch to it
        ext = options.get("ext", {1: "pgm", 3: "ppm"}.get(image.components))
        format = registry[ext](**self.config)
        return format.save(image, filename, **options)


class PAMFormat(NetpbmFormat):
    """Plugin for PAM images
    ========================

    """

    extensions = ("pam",)
    mimetypes = ("image/x-portable-anymap",)

    def open(self, image_cls, filename, **options):
        with open(filename, "rb") as fp:
            magic_number = fp.read(2)
            if magic_number != b"P7":
                format = PNMFormat(**self.config)
                return format.open(image_cls, filename, **options)
            """
            headers = defaultdict.fromkeys(list)
            for line in fp:
                line = line.strip()
                header, tokens = line.split(None, 1)
                headers[header.lower()].append(tokens)
                if line == "ENDHDR":
                    break
            for req, coercion in REQUIRED_HEADERS:
                try:
                    headers[req] = coercion(headers[req])
                except KeyError:
                    raise IOError("Missing required header {}.".format(req))
            im = image_cls(headers["tupltype"],
                           size=(headers["width"], headers["height"]))
            #read in that data
            """

    def save(self, image, filename, **options):
        pass
