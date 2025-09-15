from os.path import dirname, realpath
from setuptools import setup
import sys

name = "afmformats"

sys.path.insert(0, realpath(dirname(__file__)) + "/" + name)
try:
    from _version import version  # noqa: F821
except BaseException:
    version = "unknown"

setup(
    version=version
)
