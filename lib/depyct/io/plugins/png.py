# depyct/io/plugins/png.py
from collections import namedtuple
import ctypes
import struct
import zlib

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

# CRC: 4 byte cyclic redundancy check

class ChunkIntro(PNGStruct):
    _fields_ = [("length", ctypes.c_uint32),
                ("type", ctypes.c_char * 4)]

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


class SuggestedRGB(RGBTriple):
    _fields_ = [("frequency", ctypes.c_uint32)]


class TrueColorRGBTriple(PNGStruct):
    _fields_ = [("r", ctypes.c_uint16),
                ("g", ctypes.c_uint16),
                ("b", ctypes.c_uint16)]


class SuggestedTrueColorRGB(RGBTriple):
    _fields_ = [("frequency", ctypes.c_uint32)]


class PNGFormat(FormatBase):
    """File format plugin for PNG images
    =================================

    """

    extensions = ("png",)
    mimetypes = ("image/png",)

    def read(self):

        self.ihdr = None

        self.background_color = None
        self.phys = None

        self.palette = None
        self.suggested_palettes = {}
        self.histogram = None
        self.text = []
        self.itext = []
        self.gamma = None
        self.image_data = None
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
        return self

    def __getattr__(self, name):
        if name.startswith("_read_"):
            return self._read_unrecognized_chunk
        raise AttributeError

    def _check_crc(self):
        crc = struct.unpack(">I", self.fp.read(4))

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
        ihdr = IHDR.load(self._load_current_chunk())
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
        self.ihdr = ihdr
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

    def _read_IDAT(self):
        print("Reading in IDAT")
        self.image_data.append(self._load_current_chunk())

    def _read_IEND(self):
        print("Reading in IEND")
        self.image_data = b"".join(self.image_data)
        return "IEND"

    def _read_bKGD(self):
        print("Reading in bKGD")
        length = self.current_chunk_intro.length
        bkgd = self.current_chunk = self.fp.read(length)
        if self.ihdr.color_type == 3:
            if length != 1:
                self.fail("The background color of an indexed image must be "
                          "1 byte.")
            background_index = struct.unpack(">B", bkgd)
            self.background_color = self.palette[background_index]
        elif self.ihdr.color_type in (0, 4):
            if length != 2:
                self.fail("The background color of an grayscale image must be "
                          "2 byte.")
            self.background_color = struct.unpack(">H", bkgd)
        else: #self.ihdr.color_type in (2, 6):
            if length != 6:
                self.fail("The background color of an true color image must be "
                          "6 bytes.")
            self.background_color = TrueColorRGBTriple.load(bkgd)

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

    def _read_cHRM(self):
        print("Reading in cHRM")
        self.chroma = cHRM.load(self._load_current_chunk())
        if self.image_data:
            self.fail("cHRM block must precede image data.")
        if self.palette:
            self.fail("cHRM block must precede palette data.")

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

    def _read_tEXt(self):
        print("Reading in tEXt")
        chunk = self._load_current_chunk()
        keyword, text = chunk.split(b"\x00")
        self.text.append((keyword.decode("latin-1"), text.decode("latin-1")))

    def _read_zTXt(self):
        print("Reading in zTXt")
        chunk = self._load_current_chunk()
        keyword, data = chunk.split(b"\x00")
        compression_method, text = data[0], data[1:]
        if compression_method not in (0, b"\x00"):
            self.fail("Only compression method 0 (zlib) is supported.")
        self.text.append(keyword.decode("latin-1"),
                         zlib.decompress(text).decode("latin-1"))

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

    def _read_pHYs(self):
        print("Reading in pHYs")
        if self.phys:
            self.fail("There can be only one pHYs block per image.")
        phys = self.raw_chunk = self.fp.read(self.current_chunk_intro.length)
        self.phys = pHYs.load(phys)

    def _read_sBIT(self):
        sbit = self._load_current_chunk()
        if self.ihdr.color_type == 0:
            self.significant_bits = struct.unpack(">B", sbit)
        elif self.ihdr.color_type == 2:
            self.significant_bits = struct.unpack(">3B", sbit)
        elif self.ihdr.color_type == 3:
            self.significant_bits = struct.unpack(">3B", sbit)
        elif self.ihdr.color_type == 4:
            self.significant_bits = struct.unpack(">2B", sbit)
        elif self.ihdr.color_type == 6:
            self.significant_bits = struct.unpack(">I", sbit)
        sample_depth = 8 if self.ihdr.color_type == 3 else self.ihdr.bit_depth
        if any(s < 0 or s > sample_depth for s in self.significant_bits):
            self.fail("Significant bits exceed sample depth.")
        if image_data:
            self.fail("sBIT blocks must precede image data.")
        if palette:
            self.fail("sBIT blocks must precede palette data.")

    def _read_sPLT(self):
        print("Reading in sPLT")
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

    def _read_hIST(self):
        print("Reading in hIST")
        hist = self._load_current_chunk()
        if not self.palette:
            self.fail("hIST block must follow palette data.")
        if not len(self.palette) == len(hist) // 2:
            self.fail("Histogram must be the same size as palette.")
        self.histogram = struct.unpack(">{}H".format(len(self.palette)), hist)

    def _read_tIME(self):
        print("Reading in tIME")
        time = self._load_current_chunk()
        self.last_modified = datetime.datetime(*struct.unpack(">HBBBBB", time))

    def load(self):
        raise NotImplementedError

    def write(self):
        raise NotImplementedError
