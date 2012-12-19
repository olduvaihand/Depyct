# depyct/io/format.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
"""Image File Formats
==================

Overview paragraph on the problem, issues, and the solution we're using here.

Detailed Description of Module Contents
---------------------------------------

:data registry: A `dict` of :class:`.FormatBase` subclasses and classes
implementing the :class:`.FormatBase` interface.  The registry is keyed by the
file extensions the image formats are associated with.

Adding Custom Image :class:`.FormatBase`\ s
-------------------------------------------

Description of adding a new class with code


>>> class ABCFormat(FormatBase):
...
...    extensions = 'abc'
...
...    defaults = {'mapping': True}
...
...    _BLACK = (  0,   0,   0)
...    _RED   = (255,   0,   0)
...    _GREEN = (  0, 255,   0)
...    _BLUE  = (  0,   0, 255)
...    _WHITE = (255, 255, 255)
...
...    _open_map = {
...            b'l': _BLACK,
...            b'r': _RED, b'g': _GREEN, b'b': _BLUE,
...            b'w': _WHITE
...        }
...
...    _save_map = {
...            _BLACK: b'l',
...            _RED:   b'r', _GREEN: b'g', _BLUE: b'b',
...            _WHITE: b'w',
...        }
...
...    def open(self, filename, **options):
...        '''Read an ABC formatted image.
...        '''
...        import os
...        import struct
...
...        from depyct.image import RGB, ImageSize
...
...        with open(filename, 'rb') as fp:
...            width, height = struct.unpack('BB', fp.read(2))
...            source = [[[0]*RGB.components]*width]*height
...            lineno = 0
...            for y in range(height):
...                line = file.read(width)
...                for x in range(width):
...                    pixel = line[x]
...                    source[y][x][:] = self._open_map[pixel]
...            return Image(RGB, size=ImageSize(width, height), source=source)
...
...    def save(self, image, filename, **options):
...        '''Write an ABC formatted image.
...        '''
...        import struct
...
...        with open(filename, 'rb') as fp:
...            fp.write(struct.pack('BB', image.width, image.height))
...            for pixel in image.pixels():
...                fp.write(self._save_map[tuple(pixel)])
...
...
>>> ABCFormat in registry.values()
True
>>> import StringIO
>>>
>>> abc_format = AlphabetFormat()
>>>
>>> content = b'\x05\x05lrgbwrgbwlgbwlrbwlrgwlrgb'
>>>
>>> original = StringIO.StringIO(content)
>>> copy = StringIO.StringIO()
>>>
>>> im = abc_format.open(original)
>>> im.width == 5 and im.height == 5
True
>>> abc_format.save(im, copy)
>>> original == copy
True
"""
from abc import ABCMeta, abstractmethod, abstractproperty
import re

from depyct import util


__all__ = ['register', 'unregister', 'registry', 'FormatBase']


#FIXME: add mimetypes support to registry


class _Registry(dict):
    """The file format registry.
    """

    def register(self, cls, also=None, only=None):
        """Register :param:`cls` with image file extensions.

        :param:cls:
            :class:`.FormatBase` or a class implementing the
            `Format Interface`<_format_interface>. If :param:`only` is `None`,
            :param:`cls` must have an :attr:`extensions` attribute that is an
            iterable returning file extensions as strings. Whitespace and
            leading and trailing `.`\ s will be trimmed, in that order.
        
        :param:also:
            A string or iterable of strings that will be used **in addition**
            to those found on :param:`cls`.

        :param:only:
            A string or iterable of strings that will be used **instead of**
            those found on :param:`cls`.

        :rtype: None

        :raises: TypeError if extensions is not a string or iterable of
            strings and neither is :attr:`cls.extensions`
        :raises: AttributeError if :param:`only` is None and :param:`cls`
            lacks a propert `extensions` attribute.
        """
        extensions = self._get_extensions(cls, also, only)
        
        if all(isinstance(ext, str) for ext in extensions):
            mapping = {ext: cls for ext in extensions}
            self.update(mapping)
        else:
            raise TypeError("Extensions must be strings or iterables of "
                    "strings.")

    def unregister(self, cls, also=None, only=None):
        """Disassociate :param:`cls` from image file extensions.

        :param:cls:
            :class:`.FormatBase` or a class implementing the
            `Format Interface`<_format_interface>. If :param:`also` and
            :param:`only` are both ``None``, :param:`cls` will be entirely
            removed from the registry.
        
        :param:also:
            A string or iterable of strings that will be used **in addition**
            to those found on :param:`cls`.

        :param:only:
            A string or iterable of strings that will be used **instead of**
            those found on :param:`cls`.

        :rtype: None

        :raises: TypeError if extensions is not a string or iterable of
            strings and neither is :attr:`cls.extensions`.
        :raises: AttributeError if :param:`only` is None and :param:`cls`
            lacks a propert `extensions` attribute.
        """
        if also is None and only is None:
            to_remove = set()
            for k, v in self.items():
                if v is cls:
                    to_remove.add(k)
            for k in to_remove:
                del self[k]
        else:
            extensions = self._get_extensions(cls, also, only)

            if all(isinstance(ext, str) for ext in extensions):
                for ext in extensions:
                    self.pop(ext, None)
            else:
                raise TypeError("Extensions must be passed on the class to be "
                                "unregistered or as an explicit string or "
                                "tuple of strings.")

    def _trim_extensions(self, extensions):
        """Strip off white space and leading dots from file extension strings.

        """
        trimmed = set()
        for ext in set(extensions):
            ext = re.sub(r'^(?:\.*)([A-Za-z0-9_]*)$', lambda m: m.group(1),
                    ext.strip())
            trimmed.add(ext)
        return trimmed

    def _get_extensions(self, cls, also, only):
        """Determine the extensions to use from the registration arguments.

        """
        # FIXME: use util.string_type
        if only is not None:
            if isinstance(only, str):
                return self._trim_extensions((only,))
            else:
                return self._trim_extensions(only)
        else:
            try:
                if isinstance(cls.extensions, str):
                    cls_extensions = (cls.extensions,)
                else:
                    cls_extensions = tuple(cls.extensions)
            except AttributeError as err:
                err.message = "Image formats must have an `extensions` "\
                        "attribute that is a string or list of strings "\
                        "composed of all file extensions to be associated "\
                        "with the format."
                raise err
            if also is None:
                return self._trim_extensions(cls_extensions)
            elif isinstance(also, str):
                return self._trim_extensions(cls_extensions + (also,))
            else:
                return self._trim_extensions(cls_extensions + tuple(also))


registry = _Registry()
register = registry.register
unregister = registry.unregister


class FormatMeta(ABCMeta):
    """Metaclass for image formats.  Registers the format with
    :data:`.registry`, a mapping of file extensions to formats.

    """

    def __new__(cls, *args):
        name, bases, attrs = args
        parents = [b for b in bases if isinstance(b, FormatMeta)]
        defaults = {}
        for p in parents:
            defaults.update(p.defaults)
        defaults.update(attrs.get("defaults", {}))
        attrs["defaults"] = defaults
        cls = super(FormatMeta, cls).__new__(cls, name, bases, attrs)
        if parents:
            if isinstance(cls.extensions, str):
                register(cls, only=(cls.extensions,))
            else:
                register(cls)
        return cls


# FIXME: I'm not totally convinced that the abstract base class approach
#        is warranted here.  For instance, it would be nice to be able to
#        work directly with file pointers in all situations rather than
#        handling them within all open and close methods.  This would
#        make it much simpler to attempt to deal with files coming in off
#        sockets, for example.


#py27
class FormatBase(object):
#/py27
#py3k
#class FormatBase(metaclass=FormatMeta):
#/py3k
    """An abstract base class for image formats.

    :attr defaults: A `dict` of default configuration settings.

    :attr extensions: An iterable of strings representing the file extensions
      handled by the FormatBase class.

    """

    if util.py27:
        __metaclass__ = FormatMeta

    extensions = ()
    mimetypes = ()
    defaults = {}
    messages = {}

    def __init__(self, image_cls, **options):
        self.image_cls = image_cls
        self.config = self.update_config(**options)

    def update_config(self, **options):
        config = self.defaults.copy()
        config.update(options)
        return config

    def fail(self, message, **kwargs):
        """Raise an error.

        """
        # FIXME: it might be nice to fix the stack trace so that it starts in
        #        the calling context rather than here
        try:
            m = self.messages[message].format(**kwargs)
            raise FormatError(m)
        except KeyError:
            raise IOError(message)

    def open(self, source):
        """Load an image from `file` and return it.

        :param source: string filename or object supporting file protocol
        :rtype: :class:`~depyct.image.ImageMixin`

        """
        if isinstance(source, util.string_type):
            self.fp = open(source, "rb")
        else:
            self.fp = source
        return self.read()

    @abstractmethod
    def read(self):
        raise NotImplementedError("{}.{} is not yet implemented".format(
                                  self.__class__.__name__, "read"))

    @abstractmethod
    def load(self):
        raise NotImplementedError("{}.{} is not yet implemented".format(
                                  self.__class__.__name__, "load"))

    def save(self, image, destination):
        """Save `image` to `file`.

        :type image: :class:`~depyct.image.ImageMixin`
        :param destination: string filename or object supporting file protocol
        :rtype: None

        """
        self.image = image
        if isinstance(destination, util.string_type):
            self.fp = open(destination, "wb")
        else:
            # dealing with an open file descriptor already
            self.fp = destination
        self.write()

    @abstractmethod
    def write(self):
        raise NotImplementedError("{}.{} is not yet implemented".format(
                                  self.__class__.__name__, "write"))


def setup_format_plugins():
    import os
    from importlib import import_module

    io_directory = os.path.dirname(__file__)
    for file in os.listdir(os.path.join(io_directory, "plugins")):
        if file.endswith(".py") and not file.startswith("_"):
            module = os.path.splitext(os.path.basename(file))[0]
        else:
            continue
        import_module("depyct.io.plugins." + module)
