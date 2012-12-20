# depyct/io/plugins/gif.py
import ctypes

from depyct.image.mode import RGB
from depyct.io.format import FormatBase


class RGBTriple(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [("r", ctypes.c_byte),
                ("g", ctypes.c_byte),
                ("b", ctypes.c_byte)]


class LogicalScreenDescriptor(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [("width", ctypes.c_uint16),
                ("height", ctypes.c_uint16),
                ("global_color_table_flag", ctypes.c_uint8, 1),
                ("color_resolution", ctypes.c_uint8, 3),
                ("sort_flag", ctypes.c_uint8, 1),
                ("global_color_table_size", ctypes.c_uint8, 3),
                ("background_color_index", ctypes.c_byte),
                ("aspect_ratio", ctypes.c_byte)]


class ImageDescriptor(ctypes.LittleEndianStructure):
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


class GraphicControlExtension(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [("size", ctypes.c_byte),
                ("delay", ctypes.c_uint16),
                ("reserved", ctypes.c_uint8, 3),
                ("disposal_method", ctypes.c_uint8, 3),
                ("user_input_flag", ctypes.c_uint8, 1),
                ("transparent_color_flag", ctypes.c_uint8, 1),
                ("transparent_color_index", ctypes.c_byte),
                ("terminator", ctypes.c_byte)]


class PlainTextExtension(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [("size", ctypes.c_byte),
                ("x", ctypes.c_uint16),
                ("y", ctypes.c_uint16),
                ("width", ctypes.c_uint16),
                ("height", ctypes.c_uint16),
                ("cell_width", ctypes.c_byte),
                ("cell_height", ctypes.c_byte),
                ("foreground_color_index", ctypes.c_byte),
                ("background_color_index", ctypes.c_byte)]


class ApplicationExtension(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [("size", ctypes.c_byte),
                ("identifier", ctypes.c_byte * 8),
                ("authentication_code", ctypes.c_byte * 3)]


TRAILER = b"\x3b"
IMAGE_SEPARATOR = b"\x2c"
EXTENSION = b"\x21"
GRAPHIC_CONTROL = b"\xf9"
COMMENT = b"\xfe"
PLAIN_TEXT = b"\x01"
APPLICATION = b"\xff"


class GIFFormat(FormatBase):
    """File format plugin for GIF images
    =================================

    """

    extensions = ("gif", "gfa", "giff")
    mimetypes = ("image/gif",)

    def read(self):
        self.global_color_table = None
        self.header = self.fp.read(6)
        self.version = self.header[3:]
        lsd = self.fp.read(7)
        self.logical_screen = LogicalScreenDescriptor.from_buffer_copy(lsd)
        if self.logical_screen.global_color_table_flag:
            # read global color table
            size = self.logical_screen.global_color_table_size
            table_bytes = 3 * 2**(size+1)
            GlobalColorTable = RGBTriple * size
            self.gct = GlobalColorTable.from_buffer_copy(self.fp.read(table_bytes))
        self.size = self.logical_screen.width, self.logical_screen.height
        self.im = self.image_cls(RGB, size=self.size)
        self.comments = []
        self.plain_text = []
        self.image_data = []
        self.application_data = []
        self.load()
        return self

    def load(self):
        while True:
            block_intro = self.fp.read(1)
            # is block trailer
            if block_intro == EXTENSION:
                label = self.fp.read(1)
                if label == GRAPHIC_CONTROL:
                    size = ord(self.fp.read(1))
                    # not certain this is actually useful
                    self.fp.read(size + 1)
                elif label == COMMENT:
                    comment = []
                    while True:
                        size = ord(self.fp.read(1))
                        if size == 0:
                            break
                        comment.append(self.fp.read(size))
                    # FIXME: do something with this?
                    comment = b"".join(comment)
                    self.comments.append(comment)
                elif label == PLAIN_TEXT:
                    pte = PlainTextExtension.from_buffer_copy(
                            self.fp.read(ctypes.sizeof(PlainTextExtension)))
                    text = []
                    while True:
                        size = ord(self.fp.read(1))
                        if size == 0:
                            break
                        text.append(self.fp.read(size))
                    # FIXME: do something with this?
                    text = b"".join(text)
                    self.plain_text.append(text)
                elif label == APPLICATION:
                    ae = ApplicationExtension.from_buffer_copy(
                            self.fp.read(ctypes.sizeof(ApplicationExtension)))
                    application_data = []
                    while True:
                        size = ord(self.fp.read(1))
                        if size == 0:
                            break
                        # FIXME: do something with this?
                        application_data.append(self.fp.read(size))
                    application_data = b"".join(application_data)
                    self.application_data.append(application_data)
                else:
                    raise IOError("Unrecognized extension block label {} {}.".format(block_intro, label))
            elif block_intro == IMAGE_SEPARATOR:
                image_descriptor = ImageDescriptor.from_buffer_copy(
                        self.fp.read(ctypes.sizeof(ImageDescriptor)))
                if image_descriptor.local_color_table_flag:
                    size = self.image_descriptor.local_color_table_size
                    table_bytes = 3 * 2**(size+1)
                    LocalColorTable = RGBTriple * size
                    color_table = LocalColorTable.from_buffer_copy(
                                      self.fp.read(table_bytes))
                lzw_minimum_code_size = self.fp.read(1)
                image_data = []
                while True:
                    size = ord(self.fp.read(1))
                    if size == 0:
                        break
                    image_data.append(self.fp.read(size))
                image_data = b"".join(image_data)
                self.image_data.append(image_data)
                color_table = self.global_color_table
            elif block_intro == TRAILER:
                break
            else:
                raise IOError("Unrecognized block {}.".format(block_intro))

    def write(self):
        raise NotImplementedError
