# depyct/io/plugins/netpbm.py
import itertools
import re
import struct

from depyct.io import format
from depyct.image import mode
from depyct import util


if util.py27:
    unpack_bits = lambda chunk: [(255 if (b>>i) & 1 else 0,)
                                 for b in map(ord, chunk)
                                 for i in range(7,-1,-1)]
else:
    unpack_bits = lambda chunk: [(255 if (b>>i) & 1 else 0,) for b in chunk
                                 for i in range(7,-1,-1)]

def pack_bits(iterable, endianess="big"):
    if endianess == "big":
        range_args = (7, -1, -1)
    else:
        range_args = (8,)
    while True:
        bit = 0
        try:
            for i in range(*range_args):
                bit |= (next(iterable)<<i)
        except StopIteration:
            break
        finally:
            yield bit

def group(iterable, chunksize):
    args = [iter(iterable)] * chunksize
    return itertools.izip(*args)


class NetpbmFormat(format.FormatBase):
    """Base file format plugin for Netpbm images
    ============================================

    """

    defaults = {"format": "raw", "maxval": 255}


    def read(self):
        m = self._header_re.match(fp.read(512))
        if m is None:
            raise IOError("not a valid {}")
        self.fp.seek(m.end())
        magic_number = m.group("magic_number")
        self.size = int(m.group("width")), int(m.group("height"))
        if "maxval" in m.groupdict():
            self.maxval = maxval = int(m.group("maxval"))
            if maxval < 256:
                if magic_number in (b"P3", b"P6"):
                    self.mode = mode.RGB
                else:
                    self.mode = mode.L
            elif magic_number in (b"P3", b"P6"):
                self.mode = mode.RGB48
            else:
                self.mode = mode.L16
            bit_depth = self.mode.bits_per_component
            self.scale = lambda i: int(float(i)*((2**bit_depth) - 1) / maxval)
            self.scale_pixel = lambda p: tuple(
                    map(self.scale, p[:self.mode.components]))
        else:
            self.mode = mode.L
        im = image_cls(self.mode, size=self.size)
        try:
            data = getattr(self,
                           "_read_{}".format(self._format[magic_number]))()
        except AssertionError as err:
            raise IOError(err.message)
        im[:] = data
        return im

    def write(self):
        fmt = self.config["format"]
        magic_number = self._magic_number.get(fmt)
        header_format = b"{}\n{} {}\n"
        header = (magic_number,) + self.image.size
        if magic_number not in (b"P1", b"P4"):
            max = 2**self.image.mode.bits_per_component - 1
            self.maxval = maxval = self.config.get("maxval", max)
            bit_depth = self.image.mode.bits_per_component

            # FIXME: have something that deals with conversion
            # from one color space to another
            self.scale = lambda i: int(float(i)*((2**bit_depth) - 1) / maxval)
            if self.image.components <= 2:
                self.scale_pixel = lambda p: tuple(map(self.scale, p[:1]))
            else:
                self.scale_pixel = lambda p: tuple(map(self.scale, p[:3]))
            header_format += b"{}\n"
            header += (maxval,)
        self.fp.write(header_format.format(*header))
        try:
            # have all the info and the fp attached to the format
            data = getattr(self, "_write_{}".format(fmt))()
        except AssertionError as err:
            raise IOError(err.message)


_netpbm_header = (br"^(?P<magic_number>P[%b])\n\s*"
                  br"(?:(?:#.*?)\n\s*)??"
                  br"(?P<width>\d+)\s+"
                  br"(?:(?:#.*?)\n\s*)??"
                  br"(?P<height>\d+)\s+")
_netpbm_maxval = br"(?:(?:#.*?)\n\s*)??(?P<maxval>\d+)\s+(?:(?:#.*?)\n\s*)??"

PPM_HEADER_RE = re.compile(_netpbm_header % (br"36",) + _netpbm_maxval)


class PBMFormat(NetpbmFormat):
    """Plugin for PBM images
    ========================

    """

    extensions = ("pbm",)
    mimetypes = ("image/x-portable-bitmap",)
    defaults = {
        "clip": lambda c, image: c != image.mode.transparent_color,
    }
    messages = {
        "bad_line_data":
            "There should be no characters other than `1`, `0`, "
            "` `, and `\t` on a given scan line in pbm raster data. "
            "Check line {} of input.",
        "incorrect_width":
            "Incorrect amount of pixel data read.  Got {} pixels on "
            "line {}, expected {}.",
        "incorrect_height":
            "Incorrect number of lines read.  Got {}, expected "
            "{}."
    }

    # assert re.match("^(?:([ \t10]+)+)$", line), .format(i)
    # assert len(line_data) == width, .format(len(line_data), i, width))
    # assert len(data) == height, .format(len(data), height))

    def _read_plain(self):
        data = []
        for i, line in enumerate(self.fp): # assert 1
            line_data = [(255 if b == "1" else 0,) for b in line.split()] # assert 2
            data.append(line_data)
        return data # assert 3

    def _read_raw(self):
        data = []
        width = self.size[0]
        chunksize, padded = divmod(width, 8)
        if padded:
            chunksize += 1
        while True:
            chunk = self.fp.read(chunksize)
            if not chunk:
                break
            chunk_data = unpack_bits(chunk)[:width]
            data.append(chunk_data)
        return data

    def _write_plain(self):
        clip = self.config["clip"]
        height = self.image.size.height
        for i, line in enumerate(self.image, 1):
            self.fp.write(b" ".join(bytes(int(clip(p.value, self.image)))
                     for p in line))
            if i != height:
                self.fp.write(b"\n")

    def _write_raw(self):
        clip = self.config["clip"]
        width = self.image.size.width
        bytes_per_line, padded = divmod(width, 8)
        if padded:
            bytes_per_line += 1
        for line in self.image:
            self.fp.write(struct.pack(">{}B".format(bytes_per_line),
                     *pack_bits(clip(p.value, self.image) for p in line)))

    _header_re = re.compile(_netpbm_header % (br"14",))
    _format = {b"P1": "plain", b"P4": "raw"}
    _magic_number = {"plain": b"P1", "raw": b"P4"}


class PGMFormat(NetpbmFormat):
    """Plugin for PGM images
    ========================

    """

    extensions = ("pgm",)
    mimetypes = ("image/x-portable-graymap",)
    defaults = {}
    messages = {}

    def _read_plain(self):
        data = []
        scale = self.scale_pixel
        for line in self.fp:
            line_data = [scale((int(i),)) for i in line.split()]
            data.append(line_data)
        return data

    def _read_raw(self):
        data = []
        scale = self.scale_pixel
        width, height = self.size
        bpp = self.mode.bits_per_component // 8
        struct_format = ">{}{}".format(width, "B" if bpp == 1 else "H")
        chunksize = width * bpp
        while True:
            chunk = self.fp.read(chunksize)
            if not chunk:
                break
            line_data = [scale((p,))
                         for p in struct.unpack(struct_format, chunk)]
            data.append(line_data)
        return data

    #assert format in ("raw", "plain")
    #assert 0 < maxval < 65536
    #if image.components != 1:
        # issue a warning about loss of information

    def _write_plain(self):
        scale = self.scale
        height = self.image.size.height
        for i, line in enumerate(self.image):
            # FIXME: this is incorrect
            self.fp.write(b" ".join(bytes(scale(p.l)) for p in line))
            if i != height:
                fp.write(b"\n")

    def _write_raw(self):
        scale = self.scale
        struct_format = ">{}{}".format(self.image.size.width,
                                       "B" if self.maxval <= 255 else "H")
        for i, line in enumerate(self.image):
            # FIXME: this is incorrect
            self.fp.write(struct.pack(struct_format, *[scale(p.l)
                for p in line]))

    _header_re = re.compile(_netpbm_header % (br"25",) + _netpbm_maxval)
    _format = {b"P2": "plain", b"P5": "raw"}
    _magic_number = {"plain": b"P2", "raw": b"P5"}


class PPMFormat(NetpbmFormat):
    """Plugin for PPM images
    ========================

    """

    extensions = ("ppm",)
    mimetypes = ("image/x-portable-pixmap",)
    defaults = {}
    messages = {}

    def _read_plain(self):
        data = []
        scale = self.scale_pixel
        for line in self.fp:
            pixels = group(line.split(), 3)
            line_data = [scale(map(int, p)) for p in pixels]
            data.append(line_data)
        return data

    def _read_raw(self):
        data = []
        scale = self.scale_pixel
        bpp = self.mode.bits_per_component // 8
        width, height = self.size
        struct_format = ">{}{}".format(width*3, "B" if bpp == 1 else "H")
        chunksize = width * 3 * bpp
        while True:
            chunk = self.fp.read(chunksize)
            if not chunk:
                break
            pixels = group(struct.unpack(struct_format, chunk), 3)
            line_data = [scale(p) for p in pixels]
            data.append(line_data)
        return data

    def _write_plain(self):
        scale = self.scale_pixel
        height = self.image.size.height
        for i, line in enumerate(self.image):
            self.fp.write(b"\t".join(b" ".join(map(bytes, scale(p)))
                          for p in line))
            if i != height:
                fp.write(b"\n")

    def _write_raw(self):
        scale = self.scale_pixel
        struct_format = ">{}{}".format(self.image.size.width * 3,
                                       "B" if self.maxval <= 255 else "H")
        for i, line in enumerate(self.image):
            data = []
            for p in line:
                data.extend(scale(p))
            try:
                self.fp.write(struct.pack(struct_format, *data))
            except Exception as err:
                print(len(data))
                raise

    _header_re = re.compile(_netpbm_header % (br"36",) + _netpbm_maxval)
    _format = {b"P3": "plain", b"P6": "raw"}
    _magic_number = {"plain": b"P3", "raw": b"P6"}


class PNMFormat(NetpbmFormat):
    """Plugin for PNM images
    ========================

    """

    extensions = ("pnm",)
    mimetypes = ("image/x-portable-anymap",)
    defaults = {}
    messages = {}

    def read(self, image_cls, fp, **options):
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
        fmt = registry[ext](**self.config)
        fp.seek(0)
        return fmt.read(image_cls, fp, **options)

    def write(self, image, fp, **options):
        # FIXME: come up with a consistent way to update options
        write_options = self.update_config(**options)
        ext = write_options.get("ext",
                                {1: "pgm", 3: "ppm"}.get(image.components))
        fmt = registry[ext](**write_options)
        return fmt.write(image, fp)


class PAMFormat(NetpbmFormat):
    """Plugin for PAM images
    ========================

    """

    extensions = ("pam",)
    mimetypes = ("image/x-portable-anymap",)

    def _open(self, image_cls, fp, **options):
        magic_number = fp.read(2)
        if magic_number != b"P7":
            fmt = PNMFormat(**self.config)
            return fmt.open(image_cls, filename, **options)
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

    def _save(self, image, fp, **options):
        pass
