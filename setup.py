from os.path import dirname, realpath
from setuptools import setup
import sys

sys.path.insert(0, realpath(dirname(__file__)) + "/afmformats")
try:
    from _version import version  # noqa: F821
except BaseException:
    version = "unknown"

setup(
    version=version
)
