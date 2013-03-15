# depyct/io/plugins/png.py
from collections import namedtuple
import ctypes
import struct
import zlib

from depyct.image import mode as image_modes
from depyct.io.format import FormatBase


class PNGStruct(ctypes.BigEndianStructure):
    _pack_ = 1

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__,
                               ", ".join("{}={}".format(k, getattr(self, k))
                                         for k, t in self._fields_))
    __str__ = __repr__

    @classmethod
    def load(cls, buffer):
        if hasattr(buffer, "read"):
            buffer = buffer.read(ctypes.sizeof(cls))
        return cls.from_buffer_copy(buffer)


PNG_SIGNATURE = bytearray([137, 80, 78, 71, 13, 10, 26, 10])


class ChunkIntro(PNGStruct):
    _fields_ = [("length", ctypes.c_uint32),
                ("type", ctypes.c_char * 4)]

    @classmethod
    def load(cls, buffer):
        if hasattr(buffer, "tell"):
            offset = buffer.tell()
        else:
            offset = None
        if hasattr(buffer, "read"):
            buffer = buffer.read(ctypes.sizeof(cls))
        instance = cls.from_buffer_copy(buffer)
        instance.offset = offset
        return instance

    @property
    def critical(self):
        return self.type[0].is_upper()

    @property
    def public(self):
        return self.type[1].is_upper()

    @property
    def reserved(self):
        return self.type[2].is_upper()

    @property
    def safe_to_copy(self):
        return self.type[3].is_lower()


class IHDR(PNGStruct):
    _fields_ = [("width", ctypes.c_uint32),
                ("height", ctypes.c_uint32),
                ("bit_depth", ctypes.c_uint8),
                ("color_type", ctypes.c_uint8),
                ("compression_method", ctypes.c_uint8),
                ("filter_method", ctypes.c_uint8),
                ("interlace_method", ctypes.c_uint8)]

    BIT_DEPTHS = {
            0: (1, 2, 4, 8, 16),
            2: (8, 16),
            3: (1, 2, 4, 8),
            4: (8, 16),
            6: (8, 16)
        }


class pHYs(PNGStruct):
    _fields_ = [("x_resolution", ctypes.c_uint32),
                ("y_resolution", ctypes.c_uint32),
                ("unit", ctypes.c_byte)]


class cHRM(PNGStruct):
    _fields_ = [("white_point_x", ctypes.c_uint32),
                ("white_point_y", ctypes.c_uint32),
                ("red_x", ctypes.c_uint32),
                ("red_y", ctypes.c_uint32),
                ("green_x", ctypes.c_uint32),
                ("green_y", ctypes.c_uint32),
                ("blue_x", ctypes.c_uint32),
                ("blue_y", ctypes.c_uint32)]


iCCP = namedtuple("iCCP", "name profile")


class RGBTriple(PNGStruct):
    _fields_ = [("r", ctypes.c_uint8),
                ("g", ctypes.c_uint8),
                ("b", ctypes.c_uint8)]

    def __iter__(self):
        return iter((self.r, self.g, self.b))


class SuggestedRGB(RGBTriple):
    _fields_ = [("frequency", ctypes.c_uint32)]


class TrueColorRGBTriple(PNGStruct):
    _fields_ = [("r", ctypes.c_uint16),
                ("g", ctypes.c_uint16),
                ("b", ctypes.c_uint16)]

    def __iter__(self):
        return iter((self.r, self.g, self.b))


class SuggestedTrueColorRGB(RGBTriple):
    _fields_ = [("frequency", ctypes.c_uint32)]


def _noop(x, bpp, prior, raw):
    return raw[x]

filter_none = unfilter_none = _noop

def filter_sub(x, bpp, prior, raw):
    return raw[x] - (0 if x-bpp < 0 else raw[x-bpp])

def filter_up(x, bpp, prior, raw):
    return raw[x] - (0 if x-bpp < 0 else prior[x-bpp])

def filter_average(x, bpp, prior, raw):
    return raw[x] - ((0 if x-bpp < 0 else raw[x-bpp]) + prior[x])//2

def filter_paeth(x, bpp, prior, raw):
    if x-bpp < 0:
        prediction = paeth_predictor(0, prior[x], 0)
    else:
        prediction = paeth_predictor(raw[x-bpp], prior[x], prior[x-bpp])
    return raw[x] - prediction

def paeth_predictor(left, above, upper_left):
    p = left + above - upper_left
    pa = abs(p - left)
    pb = abs(p - above)
    pc = abs(p - upper_left)
    if pa <= pb and pa < pc:
        return left
    elif pb <= pc:
        return above
    else:
        return upper_left

def unfilter_sub(x, bpp, prior, raw):
    i = x - bpp
    return (filter_sub(x, bpp, prior, raw) + (0 if i < 0 else raw[i])) % 256

def unfilter_up(x, bpp, prior, raw):
    return (filter_up(x, bpp, prior, raw) + prior[x]) % 256

def unfilter_average(x, bpp, prior, raw):
    i = x - bpp
    return (filter_average(x, bpp, prior, raw) + 
            ((0 if i < 0 else raw[i]) + prior[x])//2) % 256

def unfilter_paeth(x, bpp, prior, raw):
    i = x - bpp
    if i < 0:
        prediction = paeth_predictor(0, prior[x], 0)
    else:
        prediction = paeth_predictor(raw[i], prior[x], prior[i])
    return (filter_paeth(x, bpp, prior, raw) + prediction ) % 256


COLOR_TYPE_L = 0
COLOR_TYPE_RGB = 2
COLOR_TYPE_PALETTE = 3
COLOR_TYPE_ALPHA = 4
COLOR_TYPE_LA = 4
COLOR_TYPE_RGBA = 6


FILTERS = {
        0: filter_none,
        1: filter_sub,
        2: filter_up,
        3: filter_average,
        4: filter_paeth
    }

UNFILTERS = {
        0: unfilter_none,
        1: unfilter_sub,
        2: unfilter_up,
        3: unfilter_average,
        4: unfilter_paeth
    }


class PNGFormat(FormatBase):
    """File format plugin for PNG images
    =================================

    """

    extensions = ("png",)
    mimetypes = ("image/png",)

    def read(self):
        self.ihdr = None
        self.image_data = []

        self.info_attrs = set()
        self.background_color = None
        self.physical_pixel_dimensions = None
        self.palette = None
        self.suggested_palettes = {}
        self.histogram = None
        self.text = []
        self.itext = []
        self.gamma = None
        self.chromaticities = None
        self.icc_profile = None
        self.significant_bits = None
        self.last_modified = None

        signature = self.fp.read(8)
        if signature != PNG_SIGNATURE:
            self.fail("unrecognized file")
        while True:
            self.current_chunk_intro = ChunkIntro.load(self.fp)
            process = getattr(self, "_read_" + self.current_chunk_intro.type)
            if process() == "IEND":
                break
            self._check_crc()

        color_type = self.ihdr.color_type
        mode_name = "RGB" if color_type & COLOR_TYPE_RGB else "L"
        if color_type & COLOR_TYPE_ALPHA:
            mode_name += "A"
        if self.ihdr.bit_depth == 16:
            mode_name += str(len(mode_name) * 16)
        mode = getattr(image_modes, mode_name)
        size = self.ihdr.width, self.ihdr.height
        im = self.image = self.image_cls(mode, size=size,
                                         color=tuple(self.background_color))
        # TODO: fill out info dictionary
        for attr in self.info_attrs:
            im.info[attr] = getattr(self, attr)
        self.load()
        return im

    def load(self):
        im = self.image
        if self.ihdr.interlace_method:
            print("Image data is interlaced.")
            self._deinterlace_pass_1()
            self._deinterlace_pass_2()
            self._deinterlace_pass_3()
            self._deinterlace_pass_4()
            self._deinterlace_pass_5()
            self._deinterlace_pass_6()
            self._deinterlace_pass_7()
        else:
            print("Image data is not interlaced.")
            self.image_data = zlib.decompress(b"".join(self.image_data))

        line_size = self.ihdr.width * 4
        bpp = 8 # calculate this properly
        prior = [0] * line_size
        for i in range(self.ihdr.height):
            filter_offset = i * (line_size + 1)
            filter_method = self.image_data[filter_offset]
            im_start = line_size * i
            im_end = im_start + line_size
            data_start = filter_offset + 1
            data_end = data_start + line_size
            unfilter = UNFILTERS[ord(filter_method)]
            # TODO: implement filter methods
            raw = self.image_data[data_start:data_end]
            raw = struct.unpack(">{}B".format(line_size), raw)
            scan = [unfilter(x, bpp, prior, raw) for x in range(line_size)]
            im.buffer[im_start:im_end] = bytearray(scan)
            prior = scan

        return im

    def __getattr__(self, name):
        if name.startswith("_read_"):
            return self._read_unrecognized_chunk
        raise AttributeError

    def _check_crc(self):
        check = zlib.crc32(self.current_chunk_intro.type + self.current_chunk)
        check &= 0xffffffff
        crc = struct.unpack(">I", self.fp.read(4))[0]
        if check != crc:
            type = self.current_chunk_intro.type
            offset = self.current_chunk_intro.offset
            self.fail("CRC failed for {} chunk at {}.".format(type, offset))

    def _load_current_chunk(self):
        self.current_chunk = self.fp.read(self.current_chunk_intro.length)
        return self.current_chunk

    def _read_unrecognized_chunk(self):
        print("Encountered {} chunk of length {} at {}.".format(
              self.current_chunk_intro.type,
              self.current_chunk_intro.length, self.fp.tell()))
        self._load_current_chunk()

    def _read_IHDR(self):
        print("Reading in IHDR")
        if self.ihdr:
            self.fail("Already encountered IHDR chunk.")
        self.ihdr = ihdr = IHDR.load(self._load_current_chunk())
        if ihdr.width == 0 or ihdr.height == 0:
            self.fail("Width and height must be specified and be "
                      "greater than 0.")
        if ihdr.color_type not in (0, 2, 3, 4, 6):
            self.fail("{} is not a valid color type.".format(
                      ihdr.color_type))
        if ihdr.bit_depth not in IHDR.BIT_DEPTHS[ihdr.color_type]:
            self.fail("{} is not valid bit depth for color type {}.".format(
                      ihdr.bit_depth, ihdr.color_type))
        if ihdr.compression_method != 0:
            self.fail("Unrecognized compression method: {}.".format(
                      ihdr.compression_method))
        if ihdr.filter_method != 0:
            self.fail("Unrecognized filter method: {}.".format(
                      ihdr.filter_method))
        if ihdr.interlace_method not in (0, 1):
            self.fail("Unrecognized interlace method: {}.".format(
                      ihdr.interlace_method))
        return ihdr

    def _read_PLTE(self):
        print("Reading in PLTE")
        plte = self._load_current_chunk()
        size = self.current_chunk_intro.length
        if self.palette:
            self.fail("Only one palette is permitted per image.")
        if size % 3:
            self.fail("Palette lenghts must be divisible by 3.")
        if self.image_data:
            self.fail("A color palette must precede image data.")
        if self.ihdr.color_type in (0, 4):
            self.fail("Images with color type {} should not have a "
                      "palette.".format(self.ihdr.color_type))
        self.palette = [RGBTriple.load(plte[i:i+3]) for i in range(size//3)]
        self.info_attrs.add("palette")

    def _read_IDAT(self):
        print("Reading in IDAT")
        self.image_data.append(self._load_current_chunk())

    def _read_IEND(self):
        print("Reading in IEND")
        return "IEND"

    def _read_bKGD(self):
        print("Reading in bKGD")
        length = self.current_chunk_intro.length
        bkgd = self.current_chunk = self.fp.read(length)
        color_type = self.ihdr.color_type
        if color_type == 3:
            if length != 1:
                self.fail("The background color of an indexed image must be "
                          "1 byte.")
            background_index = struct.unpack(">B", bkgd)
            background_color = self.palette[background_index]
        elif color_type in (0, 4):
            if length != 2:
                self.fail("The background color of an grayscale image must be "
                          "2 byte.")
            background_color = struct.unpack(">H", bkgd)
        else: #self.ihdr.color_type in (2, 6):
            if length != 6:
                self.fail("The background color of an true color image must be "
                          "6 bytes.")
            background_color = tuple(TrueColorRGBTriple.load(bkgd))

        if color_type & COLOR_TYPE_ALPHA:
            background_color += (0,)
        self.background_color = background_color
        self.info_attrs.add("background_color")

    def _read_tRNS(self):
        print("Reading in tRNS")
        color_type = self.ihdr.color_type
        trns = self._load_current_chunk()
        if self.image_data:
            self.fail("tRNS blocks must precede image data.")
        if color_type == 3:
            if not self.palette:
                self.fail("tRNS block must follow palette.")
            trns_size = len(trns) // 2
            padding = len(palette) - trns_size
            if padding < 0:
                self.fail("There must be no more than one transparency entry "
                          "per palette entry.")
            self.transparency = struct.unpack(">{}B".format(trns_size), trns)
            self.transparency += tuple(255 for i in range(padding))
        elif color_type == 0:
            self.transparency = struct.unpack(">B", trns)
        elif color_type == 2:
            self.transparency = TrueColorRGBTriple.load(trns)
        else:
            self.fail("tRNS blocks are not permitted for images with alpha "
                      "channels.") 

    def _read_gAMA(self):
        print("Reading in gAMA")
        length = self.current_chunk_intro.length
        gama = self.current_chunk = self.fp.read(length)
        self.gamma = struct.unpack(">I", gama)
        self.info_attrs.add("gamma")

    def _read_cHRM(self):
        print("Reading in cHRM")
        self.chromaticities = cHRM.load(self._load_current_chunk())
        if self.image_data:
            self.fail("cHRM block must precede image data.")
        if self.palette:
            self.fail("cHRM block must precede palette data.")
        self.info_attrs.add("chromaticities")

    def _read_sRGB(self):
        print("Reading in sRGB")
        length = self.current_chunk_intro.length
        srgb = self.current_chunk = self.fp.read(length)
        self.rendering_intent = struct.unpack(">B", srgb)
        if self.rendering_intent not in (0, 1, 2, 3):
            self.fail("Unrecognized rendering intent: {}.".format(
                      self.rendering_intent))

    def _read_iCCP(self):
        print("Reading in iCCP")
        length = self.current_chunk_intro.length
        iccp = self.current_chunk = self.fp.read(length)
        profile_name, data = iccp.split(b"\x00", 1)
        compression_method, profile = data[0], data[1:]
        if compression_method not in (0, b"\x00"):
            self.fail("Unrecognized compression method: {}.".format(
                      compression_method))
        self.icc_profile = iCCP(profile_name.decode("latin-1"),
                            zlib.decompress(profile).decode("latin-1"))
        self.info_attrs.add("icc_profile")

    def _read_tEXt(self):
        print("Reading in tEXt")
        chunk = self._load_current_chunk()
        keyword, text = chunk.split(b"\x00")
        self.text.append((keyword.decode("latin-1"), text.decode("latin-1")))
        self.info_attrs.add("text")

    def _read_zTXt(self):
        print("Reading in zTXt")
        chunk = self._load_current_chunk()
        keyword, data = chunk.split(b"\x00")
        compression_method, text = data[0], data[1:]
        if compression_method not in (0, b"\x00"):
            self.fail("Only compression method 0 (zlib) is supported.")
        self.text.append(keyword.decode("latin-1"),
                         zlib.decompress(text).decode("latin-1"))
        self.info_attrs.add("text")

    def _read_iTXt(self):
        print("Reading in iTXt")
        chunk = self._load_current_chunk()
        keyword, compression, translated_keyword, text = chunk.split(b"\x00")
        compression_flag, compression_method = compression[0], compression[1]
        language_tag = compression[2:]
        if compression_flag:
            if compression_method not in (0, b"\x00"):
                self.fail("Only compression method 0 (zlib) is supported.")
            text = zlib.decompress(text)
        self.itext.append((keyword.decode("latin-1"),
                           language_tag,
                           translated_keyword.decode("utf-8"),
                           text.decode("utf-8")))
        self.info_attrs.add("itext")

    def _read_pHYs(self):
        print("Reading in pHYs")
        if self.physical_pixel_dimensions:
            self.fail("There can be only one pHYs block per image.")
        chunk = self._load_current_chunk()
        self.physical_pixel_dimensions = pHYs.load(chunk)
        self.info_attrs.add("physical_pixel_dimensions")

    def _read_sBIT(self):
        #print("Reading in sBIT")
        color_type = self.ihdr.color_type
        bit_depth = self.ihdr.bit_depth
        sbit = self._load_current_chunk()
        sig_bits = 3 if color_type & COLOR_TYPE_RGB else 1
        if color_type & COLOR_TYPE_ALPHA:
            sig_bits += 1
        self.significant_bits = struct.unpack(">{}B".format(sig_bits), sbit)
        sample_depth = 8 if color_type & COLOR_TYPE_PALETTE else bit_depth
        if any(s < 0 or s > sample_depth for s in self.significant_bits):
            self.fail("Significant bits exceed sample depth.")
        if image_data:
            self.fail("sBIT blocks must precede image data.")
        if palette:
            self.fail("sBIT blocks must precede palette data.")
        self.info_attrs.add("significant_bits")

    def _read_sPLT(self):
        #print("Reading in sPLT")
        splt = self._load_current_chunk()
        if self.image_data:
            self.fail("sPLT blocks must precede image data.")
        name, data = splt.split(b"\x00", 1)
        name = name.decode("latin-1")
        if name in self.suggested_palettes:
            self.fail("Already encountered suggested palette named "
                      "{}.".format(name))
        sample_depth, entries = data[0], data[1:]
        if sample_depth == 8:
            entry_size, entry_struct = 6, SuggestedRGB
        elif sample_depth == 16:
            entry_size, entry_struct = 10, SuggestedTrueColorRGB
        else:
            self.fail("Sample depth must be 8 or 16.")
        num_entries, incorrect_size = divmod(len(entries))
        if incorrect_size:
            self.fail("Cannot cleanly fit {} bit samples into suggested "
                      "palette.".format(sample_depth))
        suggested_palette = [RGB.load(entries[i:i+entry_size])
                             for i in range(num_entries)]
        self.suggested_palettes[name] = suggested_palette
        self.info_attrs.add("suggested_palettes")

    def _read_hIST(self):
        #print("Reading in hIST")
        hist = self._load_current_chunk()
        if not self.palette:
            self.fail("hIST block must follow palette data.")
        if not len(self.palette) == len(hist) // 2:
            self.fail("Histogram must be the same size as palette.")
        self.histogram = struct.unpack(">{}H".format(len(self.palette)), hist)
        self.info_attrs.add("histogram")

    def _read_tIME(self):
        #print("Reading in tIME")
        time = self._load_current_chunk()
        self.last_modified = datetime.datetime(*struct.unpack(">HBBBBB", time))
        self.info_attrs.add("last_modified")

    def _deinterlace_pass_1(self):
        pass

    def _deinterlace_pass_2(self):
        pass

    def _deinterlace_pass_3(self):
        pass

    def _deinterlace_pass_4(self):
        pass

    def _deinterlace_pass_5(self):
        pass

    def _deinterlace_pass_6(self):
        pass

    def _deinterlace_pass_7(self):
        pass

    def write(self):
        raise NotImplementedError
