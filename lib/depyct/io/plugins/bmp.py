# depyct/io/plugins/bmp.py
"""
def process_image(name):
    im = open(name, "rb")
    file_header = read_bitmapfileheader(im)
    dib_header_size = unpack(integer, im)
    info_header = {12: read_bitmapcoreheader,
                   40: read_bitmapinfoheader}[dib_header_size](im)
    if info_header.compression == BI_BITFIELDS:
        masks = ColorMask(*struct.unpack("<3I", im.read(12)))
    else:
        masks = None
    if dib_header_size == 12:
        color_struct = RGBTriple
    else:
        color_struct = RGBQuad

    width, height = int(info_header.width), int(info_header.height)

    class PaletteStruct(ctypes.LittleEndianStructure):

        _fields_ = [("colors", color_struct * info_header.colors)]

    palette = PaletteStruct.from_buffer_copy(im.read(ctypes.sizeof(PaletteStruct)))

    row_size = (info_header.bits_per_pixel * width + 31) // 32 * 4
    padding = row_size - (width * info_header.bits_per_pixel) // 8


    class RowStruct(ctypes.LittleEndianStructure):
        
        _fields_ = [("pixels", ctypes.c_ubyte * width),
                    ("padding", ctypes.c_ubyte * padding)]


    class ImageStruct(ctypes.LittleEndianStructure):

        _fields_ = [("rasters", RowStruct * height)]


    image = Image(RGB, size=(width, height))

    im.seek(file_header.offset)

    image_data = ImageStruct.from_buffer_copy(im.read(info_header.image_size))

    for y, raster in enumerate(image_data.rasters):
        for x, idx in enumerate(raster.pixels):
            color = palette.colors[idx]
            image[x, height-y-1] = color.r, color.g, color.b

    return image #indices

"""
import ctypes

from depyct.io.format import FormatBase


def one_of(iterable, message):

    def check(struct, value):
        if callable(iterable):
            permitted = iterable()
        else:
            permitted = list(iterable)
        assert value in permitted, \
                self.message or "value must be one of {}".format(permitted)

    return check

def equals(allowed, message):

    def check(struct, value):
        if callable(allowed):
            permitted = allowed()
        else:
            permitted = list(allowed)
        assert value == permitted, \
                self.message or "value must be one of {}".format(permitted)




class BMPStruct(ctypes.LittleEndianStructure):

    _pack_ = 1

    @classmethod
    def read(cls, im):
        return cls.from_buffer_copy(im.read(ctypes.sizeof(cls)))

    validators = {}

    def validate(self):
        messages = {}
        for key, validator in self.validators.items():
            try:
                validator(getattr(self, key))
            except AssertionError as err:
                messages[key] = err.message
        return messages


class BMPFileHeader(BMPStruct):

    _fields_ = [("header", ctypes.c_char * 2),
                ("size", ctypes.c_uint32),
                ("reserved1", ctypes.c_uint16),
                ("reserved2", ctypes.c_uint16),
                ("offset", ctypes.c_uint32),
                ("dib_header_size", ctypes.c_uint32)]

    validators = {
    #    "header": one_of((b"BM", b"BA", b"CI", b"CP", b"IC", b"PT")),
    #    "reserved1": equals(0),
    #    "reserved2": equals(0),
    #    "dib_header_size": one_of((12, 64, 40, 52, 56, 108, 124))
    }


class BMPCoreHeader(BMPStruct):

    _fields_ = [("width", ctypes.c_uint16),
                ("height", ctypes.c_uint16),
                ("color_planes", ctypes.c_uint16),
                ("bits_per_pixel", ctypes.c_uint16)]

    validators = {
    #    "bits_per_pixel": one_of((1, 4, 8, 24)),
    }


COMPRESSION_METHODS = (
         BI_RGB, BI_RLE8, BI_REL4, BI_BITFIELDS, BI_JPEG, 
         BI_PNG, BI_ALPHABITFIELDS
     ) = range(7)


class BMPInfoHeader(BMPStruct):

    _fields_ = [("width", ctypes.c_int32),
                ("height", ctypes.c_int32),
                ("color_planes", ctypes.c_uint16),
                ("bits_per_pixel", ctypes.c_uint16),
                ("compression", ctypes.c_uint32),
                ("image_size", ctypes.c_uint32),
                ("horizontal_resolution", ctypes.c_int32),
                ("vertical_resolution", ctypes.c_int32),
                ("colors", ctypes.c_uint32),
                ("important_colors", ctypes.c_uint32)]

    validators = {
    #    "color_planes": equals(1),
    #    "bits_per_pixel": one_of((0, 1, 4, 8, 16, 24, 32)),
    #    "compression": one_of((COMPRESSION_METHODS[:6])),
        #"colors": []
    }


class BMPCoreHeader2(BMPInfoHeader):
    
    _fields_ = [("res_unit", ctypes.c_uint16),
                ("reserved", ctypes.c_uint16),
                ("orientation", ctypes.c_uint16),
                ("half_toning", ctypes.c_uint16),
                ("half_tone_size_1", ctypes.c_uint32),
                ("half_tone_size_2", ctypes.c_uint32),
                ("color_space", ctypes.c_uint32),
                ("app_data", ctypes.c_uint32)]


class FixedPoint2Dot30(BMPStruct):

    _fields_ = [("integer", ctypes.c_int32, 2),
                ("fraction", ctypes.c_int32, 30)]


class CIEXYZ(BMPStruct):

    _fields_ = [("x", FixedPoint2Dot30),
                ("y", FixedPoint2Dot30),
                ("z", FixedPoint2Dot30)]


class CIEXYZTriple(BMPStruct):

    _fields_ = [("red", CIEXYZ),
                ("green", CIEXYZ),
                ("blue", CIEXYZ)]


class RGBMask(BMPStruct):

    _fields_ = [("red_mask", ctypes.c_uint32),
                ("green_mask", ctypes.c_uint32),
                ("blue_mask", ctypes.c_uint32)]


class RGBAMask(RGBMask):

    _fields_ = [("alpha_mask", ctypes.c_uint32)]


class BMPV2InfoHeader(BMPInfoHeader):

    _fields_ = RGBMask._fields_


class BMPV3InfoHeader(BMPV2InfoHeader):

    _fields_ = RGBAMask._fields_


class BMPV4Header(BMPV3InfoHeader):

    _fields_ = [("color_space_type", ctypes.c_uint32),
                ("end_points", CIEXYZTriple),
                ("gamma_red", ctypes.c_uint32),
                ("gamma_green", ctypes.c_uint32),
                ("gamma_blue", ctypes.c_uint32)]


# assert color_space_type in BMPV4CSTYPES =\
#     LCS_CALIBRATED_RGB = 0


class BMPV5Header(BMPV4Header):

    _fields_ = [("intent", ctypes.c_uint32),
                ("profile_data", ctypes.c_uint32),
                ("profile_size", ctypes.c_uint32),
                ("reserved", ctypes.c_uint32)]


DIB_HEADERS = [
        BMPCoreHeader, BMPCoreHeader2, 
        BMPInfoHeader, BMPV2InfoHeader,
        BMPV3InfoHeader, BMPV4Header,
        BMPV5Header
]

# assert color_space_type in BMPV5CSTYPES = \
#     LCS_CALIBRATED_RGB, LCS_sRGB, LCS_WINDOWS_COLOR_SPACE, PROFILE_LINKED, PROFILE_EMBEDDED = range(5)

# assert intent in BMPV5INTENT = \
#     LCS_GM_ABS_COLORIMETRIC, LCS_GM_BUSINESS, LCS_GM_GRAPHICS, LCS_GM_IMAGES = range(4)


class RGBTriple(BMPStruct):

    _fields_ = [("b", ctypes.c_ubyte),
                ("g", ctypes.c_ubyte),
                ("r", ctypes.c_ubyte)]


class RGBQuad(RGBTriple):

    _fields_ = [("reserved", ctypes.c_ubyte)]


class BMPFormat(FormatBase):
    """

    """

    extensions = ("bmp", "dib", "rle", "2bp")
    mimetype = ("image/x-bmp",)

    def open(self, img_cls, filename, **options):
        """

        """
        im = open(filename, "rb")
        fh = BMPFileHeader.read(im)
        dib_size = fh.dib_header_size
        dib_header = {ctypes.sizeof(h) + 4: h for h in DIB_HEADERS}[dib_size]
        dh = dib_header.read(im)
        # deal with bit masks
        # determine mode
        # get size
        # read in the palette
        # calculate rowsize
        # determine if the file is large enough to have valid data
        # read in rows
        # if necessary, read in icc profile data
        

    def save(self, image, filename, **options):
        """

        """
        raise NotImplementedError

    def check(self):
        """

        """
        raise NotImplementedError

    def load(self):
        """

        """
        raise NotImplementedError
