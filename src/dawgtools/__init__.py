"""Tools for DAWG queries and data processing

This script is intended to be run using uv
(https://github.com/astral-sh/uv); follow instructions to install if
you don't have it already. Recommended method for macos and linux is

  curl -LsSf https://astral.sh/uv/install.sh | sh

"""

import glob
from os import path

__version__ = '0.1'
_data = path.join(path.dirname(__file__), 'data')


def package_data(fname, pattern=None):
    """Return the absolute path to a file included in package data,
    raising ValueError if no such file exists. If `pattern` is
    provided, return a list of matching files in package data
    (ignoring `fname`).

    """

    if pattern:
        return glob.glob(path.join(_data, pattern))

    pth = path.join(_data, fname)

    if not path.exists(pth):
        raise ValueError('Package data does not contain the file %s' % fname)

    return pth


