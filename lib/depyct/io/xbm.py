# depyct/io/xbm.py
import mmap
import re
import warnings

from depyct.image.mode import L
from .format import FormatBase

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

               bytes_per_raster = (width + 8) // 8
               fp.seek(m.end())
               map = fp.read()
               data = []
               raster = []
               for i, match in enumerate(xbm_data.finditer(map)):
                   if len(raster) < bytes_per_raster:
                       raster.append(int(match.group(0), 16))
                       continue
                   padding = width % 8
                   while raster:
                       datum = raster.pop(0)
                       if raster:
                           data.extend([255 if 1 & datum>>i else 0 for i in range(8)])
                       else:
                           data.extend([255 if 1 & datum>>i else 0 for i in range(8-padding)])
               return im, fp, data
            raise IOError("Header data not recognized.")
        except IOError as e:
            raise IOError("{} does not appear to be an XBM image: {}".format(
                          filename, e.message))

    def save(self, image, filename, **options):
        warnings.warn("XBM images do not support colors or grayscale. "
                      "By default, this format will convert images to "
                      "binary black/white images where the image mode's "
                      "transparent color will be treated as white and "
                      "everything else will be converted to black.  To "
                      "override this behavior, pass a function that "
                      "takes a single pixel as an argument as the `clip` "
                      "option.")
        print image
        if "clip" not in options:
            zero = image.mode.transparent_color
            clip = lambda p: 1 if p.value == zero else 0
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
            print line
            raster = []
            start, end = 0, 8
            while start < len(line):
                byte = 0
                for j, p in enumerate(line.pixels[start:end]):
                    print p
                    byte |= (clip(p) << j)
                raster.append(byte)
                start, end = end, end + 8
            fp.write(" " + " ".join("0x{:02x}".format(b) for b in raster) + "\n")
        fp.write("};")
