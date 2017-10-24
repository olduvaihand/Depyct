"""setup.py

Please see INSTALL.rst for basic installation instructions.

"""
import os
import re
import sys
from setuptools import setup, find_packages

if sys.version_info < (2, 7):
    raise Exception("Depyct requires Python 2.7 or higher.")

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.rst")) as readme:
    README = readme.read()

with open(os.path.join(here, "CHANGES.rst")) as changes:
    CHANGES = changes.read()

with open(os.path.join(here, "lib", "depyct", "__init__.py")) as version:
    VERSION = re.search(r'__version__ = "(.*)"', version.read(), re.S).group(1)

install_requires = [
]

tests_require = [
]

classifiers = [
    "Development Status :: 1 - Planning",
    "Intended Audience :: Developers",
    "Topic :: Multimedia :: Graphics",
    "Topic :: Multimedia :: Graphics :: Editors",
    "Topic :: Multimedia :: Graphics :: Editors :: Raster-Based",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: Jython",
    "Programming Language :: Python :: Implementation :: PyPy"
]

setup(name="Depyct",
      version=VERSION,
      author="Ben Trofatter",
      author_email="trofatter@google.com",
      url="http://www.depyct.org",
      description="Image Creation and Manipulation Library",
      long_description=README + "\n\n" + CHANGES,
      classifiers=classifiers,
      packages=find_packages("lib"),
      package_dir={"": "lib"},
      install_requires=install_requires,
      tests_require=tests_require,
      license="MIT License",
      zip_safe=False,
      entry_points=""
  )
