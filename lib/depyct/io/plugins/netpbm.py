# depyct/io/plugins/netpbm.py
import enum
import itertools
import re
import struct

from depyct.io import format
from depyct import image
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
    return zip(*(iter(iterable),) * chunksize)


def affine(a, i, I, o, O):
    return int(O - float((I - a)*(O - o))/(I - i))


class MagicNumber(enum.Enum):

    PLAIN_PBM = b"P1"
    PLAIN_PGM = b"P2"
    PLAIN_PPM = b"P3"
    RAW_PBM = b"P4"
    RAW_PGM = b"P5"
    RAW_PPM = b"P6"
    PAM = b"P7"

    @classmethod
    def from_string(cls, s):
        try:
            return {v, e for e, v in cls.__members__.items()}[s]
        except KeyError:
            raise ValueError("{} is not a valid NetPBM magic number".format(s))


class PamHeader:

    def __init__(self, fp):
        self._fp = fp
        self._magic_number = None
        self._width = None
        self._height = None
        self._maxval = None
        self.comments = []
        self.headers = {}
        self._last_line = None
        self._parse()

    def _parse(self):
        self._read_magic_number()
        if self.magic_number is MagicNumber.PAM:
            self._read_pam_header()
        else:
            self._read_pnm_header()

    @property
    def magic_number(self):
        return MagicNumber.from_string(self._magic_number)

    @property
    def mode(self):
        return self._mode

    @property
    def size(self):
        return image.ImageSize(self._width, self._height)

    def _read_magic_number(self):
        self._magic_number = self._fp.read(2)

    def _read_pam_header(self):
        required_headers = {b"WIDTH", b"HEIGHT", b"DEPTH", b"MAXVAL"}
        for line in self.fp:
            line = line.strip()
            if not line:
                continue
            elif line.startswith(b"#"):
                self.comments.append(line)
                continue
            elif line == b"ENDHDR":
                break
            name, value = line.split(None, 1)
            self._handle_pam_header(name, value)
        self._check_pam_errors()
        self._get_pam_mode()

    def _read_pnm_header(self):
        self._read_pnm_comments()
        self._read_pnm_width()
        self._read_pnm_comments()
        self._read_pnm_height()
        self._read_pnm_comments()
        self._read_pnm_maxval()
        self._read_pnm_comments()

    def _handle_pam_header(self, name, value):
        if name == b"WIDTH":
            self.required_headers.remove(name)
            self._width = int(token)
        elif name == b"HEIGHT":
            self.required_headers.remove(name)
            self._height = int(token)
        elif name == b"DEPTH":
            self.required_headers.remove(name)
            self._depth = int(token)
        elif name == b"MAXVAL":
            self.required_headers.remove(name)
            self._maxval = int(token)
        elif name == b"TULTYPE":
            self._headers.setdefault(header, []).append(token)
        else:
            self._headers[header] = token

    def _get_pam_mode(self):
        bytes_per_component = 8 if self._maxval < 2**8 else 16
        if self._depth = 1:
            self._mode = mode.L if bytes_per_component == 8 else mode.L16
        elif self._depth = 2:
            self._mode = mode.LA if bytes_per_component == 8 else mode.LA32
        elif self._depth = 3:
            self._mode = mode.RGB if bytes_per_component == 8 else mode.RGB48
        elif self._depth = 4:
            self._mode = mode.RGBA if bytes_per_component == 8 else mode.RGBA64
        else:
            raise NotImplementedError(
                    "Depyct doesn't support images with more than 4 channels")

    def _read_pnm_comments(self)
        while True:
            self._last_line = self._fp.readline().strip()
            if not self._last_line:
                continue
            if not self._last_line.startswith(b"#"):
                return
            self.comments.append(self._last_line)

    def _read_pnm_width(self):
        self._width = self._read_pnm_header_field()

    def _read_pnm_height(self):
        self._height = self._read_pnm_header_field()

    def _read_pnm_maxval(self):
        self._maxval = self._read_pnm_header_field()

    def _read_pnm_header_field(self):
        tokens = [t.strip() for t in self._last_line.split(n'#')]
        value = int(tokens[0])
        if len(tokens) > 1:
            self.comments.extend(tokens[1:])
        return value


class PamFormat(format.FormatBase):

    defaults = {"format": "raw"}

    def read(self):
        self._header = PamHeader(self.fp)

        im = self.image_cls(self._header.mode, size=self._header.size)

        im[:] = {
                MagicNumber.PLAIN_PBM: self._read_plain_pnm,
                MagicNumber.PLAIN_PGM: self._read_plain_pnm,
                MagicNumber.PLAIN_PPM: self._read_plain_pnm,
                MagicNumber.RAW_PBM: self._read_raw_pbm,
                MagicNumber.RAW_PGM: self._read_pam,
                MagicNumber.RAW_PPM: self._read_pam,
                MagicNumber.PAM: self._read_pam,
        }[self._header.magic_number]()

        return im

    def _read_plain_pnm(self):
        data = []
        for line in self.fp:
            data.append([tuple(int(c) for c in p)
                for p in group(line.split(), self._header.mode.components)])
        return data

    def _read_raw_pbm(self):
        data = []
        width, _ = self._header.size
        chunksize, padded = divmod(width, 8)
        if padded:
            chunksize += 1
        while True:
            chunk = self.fp.read(chunksize)
            if not chunk:
                break
            line_data = unpack_bits(chunk)[:width]
            data.append(chunk_data)
        return data

    def _read_pam(self):
        data = []
        components = self._header.mode.components
        bpp = self._header.mode.bytes_per_pixel
        width, _ = self._header.size
        struct_format = ">{}{}".format(
            width * components, "B" if bpp == 1 else "H")
        chunksize = width * bpp
        while True:
            chunk = self.fp.read(chunksize)
            if not chunk:
                break
            line_data = list(group(
                struct.unpack(struct_format, chunk), components))
            data.append(line_data)
        return data

'''


class NetpbmFormat(format.FormatBase):
    """Base file format plugin for Netpbm images
    ============================================

    """

    defaults = {"format": "raw", "maxval": 255}


    def read(self):
        m = self._header_re.match(self.fp.read(512))
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
            self.scale = lambda a: affine(a, 0, maxval, 0, 2**bit_depth - 1)
            self.scale_pixel = lambda p: tuple(
                    map(self.scale, p[:self.mode.components]))
        else:
            self.mode = mode.L
        im = self.image_cls(self.mode, size=self.size)
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
        header_format = b"%b\n%d %d\n"
        header = (magic_number,) + self.image.size
        if magic_number not in (b"P1", b"P4"):
            max = 2**self.image.mode.bits_per_component - 1
            self.maxval = maxval = self.config.get("maxval", max)
            bit_depth = self.image.mode.bits_per_component

            # FIXME: have something that deals with conversion
            # from one color space to another
            self.scale = lambda a: affine(a, 0, 2**bit_depth - 1, 0, maxval)
            if self.image.components <= 2:
                self.scale_pixel = lambda p: tuple(map(self.scale, p[:1]))
            else:
                self.scale_pixel = lambda p: tuple(map(self.scale, p[:3]))
            header_format += b"%d\n"
            header += (maxval,)
        self.fp.write(header_format % header)
        try:
            # have all the info and the fp attached to the format
            data = getattr(self, "_write_{}".format(fmt))()
        except AssertionError as err:
            raise IOError(err.message)


_NETPBM_HEADER = (br"^(?P<magic_number>P[%b])\n\s*"
                  br"(?:(?:#.*?)\n\s*)??"
                  br"(?P<width>\d+)\s+"
                  br"(?:(?:#.*?)\n\s*)??"
                  br"(?P<height>\d+)\s+")
_NETPBM_MAXVAL = br"(?:(?:#.*?)\n\s*)??(?P<maxval>\d+)\s+(?:(?:#.*?)\n\s*)??"


class PbmFormat(NetpbmFormat):
    """Plugin for PBM images
    ========================

    """

    extensions = ("pbm",)
    mimetypes = ("image/x-portable-bitmap",)
    defaults = {
        "clip": lambda c, im: c != im.mode.transparent_color,
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
            line_data = [(255 if b == b"1" else 0,) for b in line.split()] # assert 2
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
        row_template = b"\t".join((b"%d",) * self.image.size.width)
        height = self.image.size.height
        for i, line in enumerate(self.image, 1):
            row = row_template % tuple(
                    int(clip(p.value, self.image)) for p in line)
            self.fp.write(row)
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

    _header_re = re.compile(_NETPBM_HEADER % (br"14",))
    _format = {b"P1": "plain", b"P4": "raw"}
    _magic_number = {"plain": b"P1", "raw": b"P4"}


class PgmFormat(NetpbmFormat):
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
        row_template = b"\t".join((b"%d",) * self.image.size.width)
        for i, line in enumerate(self.image):
            row = row_template % tuple(scale(p.l) for p in line)
            self.fp.write(row)
            if i != height:
                self.fp.write(b"\n")

    def _write_raw(self):
        scale = self.scale
        struct_format = ">{}{}".format(self.image.size.width,
                                       "B" if self.maxval <= 255 else "H")
        for i, line in enumerate(self.image):
           self.fp.write(struct.pack(struct_format, *[scale(p.l)
                for p in line]))

    _header_re = re.compile(_NETPBM_HEADER % (br"25",) + _NETPBM_MAXVAL)
    _format = {b"P2": "plain", b"P5": "raw"}
    _magic_number = {"plain": b"P2", "raw": b"P5"}


class PpmFormat(NetpbmFormat):
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
            line_data = [scale(tuple(int(_) for _ in p)) for p in pixels]
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
        row_template = b"\t".join((b"%d\t%d\t%d",) * self.image.size.width)
        for i, line in enumerate(self.image):
            format_args = tuple(
                    itertools.chain.from_iterable(scale(p.value) for p in line))
            row = row_template % format_args
            self.fp.write(row)
            if i != height:
                self.fp.write(b"\n")

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

    _header_re = re.compile(_NETPBM_HEADER % (br"36",) + _NETPBM_MAXVAL)
    _format = {b"P3": "plain", b"P6": "raw"}
    _magic_number = {"plain": b"P3", "raw": b"P6"}


class PnmFormat(NetpbmFormat):
    """Plugin for PNM images
    ========================

    """

    extensions = ("pnm",)
    mimetypes = ("image/x-portable-anymap",)
    defaults = {}
    messages = {}

    def read(self):
        magic_number = self.fp.read(2)
        try:
            ext = {b"P1": "pbm", b"P4": "pbm",
                   b"P2": "pgm", b"P5": "pgm",
                   b"P3": "ppm", b"P6": "ppm"}[magic_number]
        except KeyError:
            raise IOError("Unrecognized magic number {} for pnm format. "
                          "Should be P1, P2, or P3 for plain text pbm, "
                          "pgm, or ppm, respectively, or P4, P5, or P6 for "
                          "raw pbm, pgm, or ppm, respectively.".format(
                              magic_number))
        fmt = format.registry[ext](self.image_cls, **self.config)
        # Seeking isn't always an option. Is there any way to skip reading
        # the magic number in the other formats?
        self.fp.seek(0)
        return fmt.open(self.fp)

    def write(self):
        if self.image.components <= 2:
            ext = "pgm"
        else:
            ext = "ppm"
        fmt = format.registry[ext](self.image_cls, **self.config)
        return fmt.save(self.image, self.fp)


class PamFormat(NetpbmFormat):
    """Plugin for PAM images
    ========================

    """

    extensions = ("pam",)
    mimetypes = ("image/x-portable-arbitrarymap",)

    REQUIRED_HEADERS = {b"HEIGHT", b"WIDTH", b"DEPTH", b"MAXVAL"}

    def read(self):

        def debug(o):
            print("DEBUG!")
            print(o)
            print("DEBUG!")

        magic_number = self.fp.read(2)
        if magic_number != b"P7":
            fmt = PNMFormat(image_cls, **self.config)
            # FIXME: remove this seek or wrap the fp in a buffered object
            self.fp.seek(0)
            return fmt.open(self.fp)

        headers = {}
        for line in self.fp:
            line = line.strip()
            if not line or line.startswith(b'#'):
                continue
            if line == b"ENDHDR":
                break
            header, token = line.split(None, 1)
            if header == b"TUPLYPE":
                headers.setdefault(header, []).append(token)
            elif header in headers:
                raise ValueError(
                        "Header includes more than one {} line: {}, {}".format(
                            header, self.headers[header], token))
            else:
                headers[header] = token

        for required in self.REQUIRED_HEADERS:
            if required not in headers:
                raise ValueError(
                        "Required header {} was missing".format(required))

        maxval = int(headers[b"MAXVAL"])
        if maxval < 2**8:
            bit_depth = 8
        elif maxval < 2**16:
            bit_depth = 16
        else:
            raise ValueError("MAXVAL too high: {}".format(maxval))
        components = int(headers[b"DEPTH"])

        im_mode = {
            8:  {1: mode.L,   2: mode.LA,    3: mode.RGB,    4: mode.RGBA},
            16: {1: mode.L16, 2: mode.LA32,  3: mode.RGB48,  4: mode.RGBA64},
        }[bit_depth][components]

        size = image.ImageSize(int(headers[b"WIDTH"]), int(headers[b"HEIGHT"]))
        im = self.image_cls(im_mode, size)

        if im_mode == mode.L:
          debug(im.buffer.tobytes())
          debug(im.buffer.shape)
        data = self.fp.read()
        if im_mode == mode.L:
          debug(len(data))
          debug(data)
        im.buffer[:] = data

        im.map(lambda v: affine(v, 0, maxval, 0, 2**bit_depth - 1))

        return im

    def write(self):
        pass
'''
