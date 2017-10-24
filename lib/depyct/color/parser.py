# depyct/color/parser.py
# Copyright (c) 2012-2017 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
"""
Formats:

    l(1)
    la(1, 2)
    rgb(1, 2, 3)
    hsv(1, 2, 3)
    hsl(1, 2, 3)
    rgba(1, 2, 3, 4)
    cmyk(1, 2, 3, 4)
    #aaa
    #aaaaaa

"""
import re

l_re = re.compile(r"^l\((\d+)\)$")
la_re = re.compile(r"^la\((\d+),(\d+)\)$")
rgb_re = re.compile(r"^rgb\((\d+),(\d+),(\d+)\)$")
hsv_re = re.compile(r"^hsv\((\d+),(\d+),(\d+)\)$")
hsl_re = re.compile(r"^hsl\((\d+),(\d+),(\d+)\)$")
rgba_re = re.compile(r"^rgba\((\d+),(\d+),(\d+),(\d+)\)$")
cmyk_re = re.compile(r"^cmyk\((\d+),(\d+),(\d+),(\d+)\)$")
web_short_re = re.compile(r"^#([\da-fA-F])([\da-fA-F])([\da-fA-F])$")
web_long_re = re.compile(r"^#([\da-fA-F]{2})([\da-fA-F]{2})([\da-fA-F]{2})$")

color_regexes = {
        "l": l_re,
        "la": la_re,
        "rgb": rgb_re,
        "hsv": hsv_re,
        "hsl": hsl_re,
        "rgba": rgba_re,
        "cmyk": cmyk_re
    }

test_values = [
    (l_re, "l(10)"),
    (la_re, "la(10,100)"),
    (rgb_re, "rgb(10,20,30)"),
    (hsv_re, "hsv(10,20,30)"),
    (hsl_re, "hsl(10,20,30)"),
    (rgba_re, "rgba(10,20,30,40)"),
    (cmyk_re, "cmyk(10,20,30,40)"),
    (web_short_re, "#341"),
    (web_long_re, "#a7882d"),
    ]


def parse_color_string(color):
    try:
        if color.startswith("#"):
            if len(color) == 4:
                m = web_short_re.match(color)
                res = tuple(int(c*2, 16) for c in m.groups())
            else:
                m = web_long_re.match(color)
                res = tuple(int(c, 16) for c in m.groups())
            return "web", res
        else:
            prefix = color.split("(")[0]
            regex = color_regexes[prefix]
            m = regex.match(color)
            return prefix, tuple(int(c) for c in m.groups())
    except:
        raise ValueError("Not a valid color")


if __name__ == "__main__":
    for _, color in test_values:
        try:
            print(parse_color_string(color))
        except ValueError:
            print("{} didn't parse".format(color))
