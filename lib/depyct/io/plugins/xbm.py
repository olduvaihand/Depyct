# depyct/io/plugins/xbm.py
import mmap
import re
import warnings

from depyct.image.mode import L
from depyct.io.format import FormatBase

xbm_header = re.compile(
        br"(?:/\*.*\*/)?"
        br"\s*#[ \t]*define[ \t]+[A-Za-z0-9_]*_width[ \t]+(?P<width>\d+)[\r\n]+"
        br"(?:/\*.*\*/)?"
        br"\s*#[ \t]*define[ \t]+[A-Za-z0-9_]*_height[ \t]+(?P<height>\d+)[\r\n]+"
        br"(?:/\*.*\*/)?"
        br"(?P<hotspot> "
        br"(?:/\*.*\*/)?"
        br"\s*#[ \t]*define[ \t]+[A-Za-z0-9_]*_x_hot[ \t]+(?P<x_hot>\d+)[\r\n]+"
        br"(?:/\*.*\*/)?"
        br"\s*#[ \t]*define[ \t]+[A-Za-z0-9_]*_y_hot[ \t]+(?P<y_hot>\d+)[\r\n]+"
        br"(?:/\*.*\*/)?"
        br")?"
        br"(?:/\*.*\*/)?"
        br"\s*[A-Za-z\d \t]*_bits\[\][ \t]+=[ \t]+"
   )

xbm_data = re.compile(br"(0x[0-9a-fA-F]{2})")

class XBMFormat(FormatBase):
    """File format plugin for XBM images
    =================================

    Description of Format
    =====================
    XBMs are commonly saved in header files to be included in source.  In
    addition to the required `width` and `height` preprocessor definitions,
    they can also optionally have a `x_hot` and `y_hot` pair, which represent
    the coordinates of the active point on the screen when the image is loaded 
    into e.g.  an X-11 application.  The image data follows as an array of 
    chars named `bits`.

    #define {optional_name}_width 16
    #define {optional_name}_height 16
    #define {optional_name}_x_hot 1
    #define {optional_name}_y_hot 1
    static char _bits[] = {
    };
    
    """

    extensions = ("xbm",)
    mimetypes = ("image/x-xbm", "image/x-xbitmap")

    def open(self, image_cls, filename, **options):
        fp = open(filename, "rb")
        m = xbm_header.match(fp.read(1024))
        try:
            if m:
               width = int(m.group("width"))
               height = int(m.group("height"))
               im = image_cls(L, size=(width, height))
               if m.group("hotspot"):
                   im.info["hotspot"] = (int(m.group("x_hot")),
                                         int(m.group("y_hot")))
               padding = width % 8
               bytes_per_raster = width // 8 + (1 if padding else 0)
               fp.seek(m.end())
               map = fp.read()
               data = []
               raster = []
               for i, match in enumerate(xbm_data.finditer(map)):
                   raster.append(int(match.group(0), 16))
                   if len(raster) < bytes_per_raster:
                       continue
                   while raster:
                       byte = raster.pop(0)
                       if raster:
                           pixels = [(255 if (1 & (byte>>i)) else 0)
                                     for i in range(8)]
                       else:
                           pixels = [(255 if (1 & (byte>>i)) else 0)
                                     for i in range(padding)]
                       data.extend(pixels)
               try:
                   im.buffer[:] = bytearray(data)
               except ValueError:
                   raise IOError("Read an unexpected amount of data. "
                                 "Expected {} bits, received {}.".format(
                                     width * height, len(data)))
               else:
                   return im
            raise IOError("Header data not recognized.")
        except IOError as e:
            raise IOError("{} does not appear to be a valid XBM image: "
                          "{}".format(filename, e.message))

    def save(self, image, filename, **options):
        warnings.warn("XBM images do not support colors or grayscale. "
                      "By default, this format will convert images to "
                      "binary black/white images where the image mode's "
                      "transparent color will be treated as white and "
                      "everything else will be converted to black.  To "
                      "override this behavior, pass a function that "
                      "takes a single pixel as an argument as the `clip` "
                      "option.")
        if "clip" not in options:
            clip = lambda p: 0 if tuple(p) == image.mode.transparent_color else 1
        else:
            clip = option["clip"]
        fp = open(filename, "wb")
        label = options.get("label", "")
        fp.write("#define {}_width {}\n".format(label, image.size.width))
        fp.write("#define {}_height {}\n".format(label, image.size.height))
        if image.info.get("hotspot"):
            hotspot = image.info["hotspot"]
            fp.write("#define {}_x_hot {}\n".format(label, hotspot[0]))
            fp.write("#define {}_y_hot {}\n".format(label, hotspot[1]))
        fp.write("static char {}_bits[] = {{\n".format(label))
        for i, line in enumerate(image):
            raster = []
            start, end = 0, 8
            while start < len(line):
                byte = 0
                for j, p in enumerate(line.pixels[start:end]):
                    byte |= (clip(p) << j)
                raster.append(byte)
                start, end = end, end + 8
            fp.write(" " + " ".join("0x{:02x}".format(b) for b in raster) + "\n")
        fp.write("};\n")
