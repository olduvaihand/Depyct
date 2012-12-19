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
                ("transparent_color_index", ctypes.c_byte)]


TERMINATOR = b"\3b"
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
        self.load()

    def load(self):
        while True:
            block_intro = self.fp.read(1)
            # is block trailer
            if block_intro == EXTENSION:
                label = self.fp.read(1)
                if label == GRAPHIC_CONTROL:
                    pass
                elif label == COMMENT:
                    pass
                elif label == PLAIN_TEXT:
                    pass
                elif label == APPLICATION:
                    pass
                else:
                    raise IOError("Unrecognized extension block label.")

            elif block_intro == IMAGE_SEPARATOR:
        #       if block has graphic control extension:
        #           read gce
        #       if block is table based image:
        #           read image descriptor
        #           if local color table:
        #               push global color table
        #               read local color table
        #           read image data
        #           pop local color table
        #       else:
        #          read plain text extension
            elif block_intro == TERMINATOR:
                print "hit the terminator"
                break
            else:
                raise IOError("Unrecognized block.")

    def write(self):
        raise NotImplementedError
