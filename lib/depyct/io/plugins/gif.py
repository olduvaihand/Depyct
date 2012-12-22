# depyct/io/plugins/gif.py
import ctypes

from depyct.image.mode import RGB
from depyct.io.format import FormatBase


class GIFStruct(ctypes.LittleEndianStructure):
    _pack_ = 1

    @classmethod
    def load(cls, fp):
        return cls.from_buffer_copy(fp.read(ctypes.sizeof(cls)))

    def write(self, fp):
        pass


class GIFHeader(GIFStruct):
    _pack_ = 1
    _fields_ = [("signature", ctypes.c_char * 3),
                ("version", ctypes.c_char * 3)]


class LogicalScreenDescriptor(GIFStruct):
    _pack_ = 1
    _fields_ = [("width", ctypes.c_uint16),
                ("height", ctypes.c_uint16),
                ("global_color_table_flag", ctypes.c_uint8, 1),
                ("color_resolution", ctypes.c_uint8, 3),
                ("sort_flag", ctypes.c_uint8, 1),
                ("global_color_table_size", ctypes.c_uint8, 3),
                ("background_color_index", ctypes.c_uint8),
                ("aspect_ratio", ctypes.c_uint8)]


class RGBTriple(GIFStruct):
    _pack_ = 1
    _fields_ = [("r", ctypes.c_uint8),
                ("g", ctypes.c_uint8),
                ("b", ctypes.c_uint8)]


class ImageDescriptor(GIFStruct):
    _pack_ = 1
    _fields_ = [("x", ctypes.c_uint16),
                ("y", ctypes.c_uint16),
                ("width", ctypes.c_uint16),
                ("height", ctypes.c_uint16),
                ("local_color_table_flag", ctypes.c_uint8, 1),
                ("interface_flag", ctypes.c_uint8, 1),
                ("sort_flag", ctypes.c_uint8, 1),
                ("reserved", ctypes.c_uint8, 2),
                ("local_color_table_size", ctypes.c_uint8, 3)]


class GraphicControlExtension(GIFStruct):
    _pack_ = 1
    _fields_ = [("size", ctypes.c_byte),
                ("delay", ctypes.c_uint16),
                ("reserved", ctypes.c_uint8, 3),
                ("disposal_method", ctypes.c_uint8, 3),
                ("user_input_flag", ctypes.c_uint8, 1),
                ("transparent_color_flag", ctypes.c_uint8, 1),
                ("transparent_color_index", ctypes.c_uint8),
                ("terminator", ctypes.c_uint8)]


class PlainTextExtension(GIFStruct):
    _pack_ = 1
    _fields_ = [("size", ctypes.c_uint8),
                ("x", ctypes.c_uint16),
                ("y", ctypes.c_uint16),
                ("width", ctypes.c_uint16),
                ("height", ctypes.c_uint16),
                ("cell_width", ctypes.c_byte),
                ("cell_height", ctypes.c_byte),
                ("foreground_color_index", ctypes.c_uint8),
                ("background_color_index", ctypes.c_uint8)]


class ApplicationExtension(GIFStruct):
    _pack_ = 1
    _fields_ = [("size", ctypes.c_uint8),
                ("identifier", ctypes.c_char * 8),
                ("authentication_code", ctypes.c_char * 3)]


TRAILER = b"\x3b"
IMAGE_SEPARATOR = b"\x2c"
EXTENSION = b"\x21"
GRAPHIC_CONTROL_EXTENSION = b"\xf9"
COMMENT_EXTENSION = b"\xfe"
PLAIN_TEXT_EXTENSION = b"\x01"
APPLICATION_EXTENSION = b"\xff"


class GIFFormat(FormatBase):
    """File format plugin for GIF images
    =================================

    """

    extensions = ("gif", "gfa", "giff")
    mimetypes = ("image/gif",)

    def __init__(self, image_cls, **config):
        super(GIFFormat, self).__init__(image_cls, **config)
        self.graphic_controls = []
        self.global_color_table = None
        self.active_color_table = None
        self.comments = []
        self.plain_text = []
        self.images = []
        self.application_data = []

    def read(self):
        self.header = GIFHeader.load(self.fp)
        self.logical_screen = LogicalScreenDescriptor.load(self.fp)
        if self.logical_screen.global_color_table_flag:
            # read global color table
            size = self.logical_screen.global_color_table_size
            ncolors = 2 ** (size + 1)
            GlobalColorTable = type("GlobalColorTable", (GIFStruct,), {
                    "_fields_": [("colors", RGBTriple * ncolors)]
                })
            self.global_color_table = GlobalColorTable.load(self.fp)
            self.active_color_table = self.global_color_table
        self.size = self.logical_screen.width, self.logical_screen.height
        self.im = self.image_cls(RGB, size=self.size)
        self.load()
        return self

    def load(self):
        while True:
            block_intro = self.fp.read(1)
            if block_intro == EXTENSION:
                label = self.fp.read(1)
                if label == GRAPHIC_CONTROL_EXTENSION:
                    self._load_graphic_control_extension()
                elif label == COMMENT_EXTENSION:
                    self._load_comment()
                elif label == PLAIN_TEXT_EXTENSION:
                    self._load_plain_text()
                elif label == APPLICATION_EXTENSION:
                    self._load_application_extension()
                else:
                    # FIXME: use message system
                    raise IOError("Unrecognized extension block label at "
                                  "offset {}: {} {}.".format(
                                  self.fp.tell(), block_intro, label))
            elif block_intro == IMAGE_SEPARATOR:
                self._load_image()
            elif block_intro == TRAILER:
                break
            else:
                # FIXME: use message system
                raise IOError("Unrecognized block at {}: {}.".format(
                              self.fp.tell(), block_intro))

    def _load_graphic_control_extension(self):
        gce = GraphicControlExtension.load(self.fp)
        self.graphic_controls.append(gce)

    def _load_comment(self):
        comment = []
        while True:
            size = ord(self.fp.read(1))
            if size == 0:
                break
            comment.append(self.fp.read(size))
        comment = b"".join(comment)
        self.comments.append(comment)

    def _load_plain_text(self):
        pte = PlainTextExtension.load(self.fp)
        text = []
        while True:
            size = ord(self.fp.read(1))
            if size == 0:
                break
            text.append(self.fp.read(size))
        text = b"".join(text)
        self.plain_text.append(text)

    def _load_application_extension(self):
        ae = ApplicationExtension.load(self.fp)
        application_data = []
        while True:
            size = ord(self.fp.read(1))
            if size == 0:
                break
            application_data.append(self.fp.read(size))
        application_data = b"".join(application_data)
        self.application_data.append(application_data)

    def _load_color_table(self, size):
        ncolors = 2 ** (size + 1)
        ColorTable = type("ColorTable", (GIFStruct,), {
                "_fields_": [("colors", RGBTriple * ncolors)]
            })
        return ColorTable.load(self.fp)

    def _load_image(self):
        image_descriptor = ImageDescriptor.load(self.fp)
        if image_descriptor.local_color_table_flag:
            self.active_color_table = self._load_color_table(
                                    image_descriptor.local_color_table_size)
        lzw_minimum_code_size = self.fp.read(1)
        image_blocks = []
        while True:
            size = ord(self.fp.read(1))
            if size == 0:
                break
            image_blocks.append(self.fp.read(size))
        image_data = b"".join(image_blocks)
        self._decompress_image(image_data)
        color_table = self.global_color_table

    def _decompress_image(self, image_data):
        # TODO: LZW Decompression goes in right about here
        self.images.append(image_data)

    def write(self):
        self._write_header()
        self._write_logical_screen_descriptor()

    def _write_header(self):
        # determine gif version
        version = b"89a"
        header = GIFHeader(signature=b"GIF", version=version)
        # TODO: figure out how to write structs to file

    def _write_logical_screen_descriptor(self):
        width, height = self.image.size
        lsd = LogicalScreenDescriptor(width=width, height=height)
        
        if True:
            # will there be a global color table?
            lsd.global_color_table_flag = 1
            # how many colors will be in it?
            # count the colors and reverse the size calculation
            lsd.global_color_table_size = 7
        else:
            lsd.global_color_table_flag = 0
            lsd.global_color_table_size = 0

        #lsd.color_resolution
        #lsd.sort_flag
        #lsd.background_color_index
        lsd.aspect_ratio = self.image.info.get("aspect_ratio", 0)
