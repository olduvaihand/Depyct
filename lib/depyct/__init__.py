# depyct/__init__.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
"""

"""
from .image.mode import *
from .image import *
from .io.format import setup_format_plugins

#setup_format_plugins()

__version__ = "0.0.1a1"
__all__ = image.mode.__all__ + image.__all__
