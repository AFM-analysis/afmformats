from os.path import dirname, exists, realpath
from setuptools import setup, find_packages
import sys

author = "Paul Müller"
authors = [author, "Shada Abuhattum"]
description = 'reading common AFM file formats'
name = 'afmformats'
year = "2019"


sys.path.insert(0, realpath(dirname(__file__))+"/"+name)
try:
    from _version import version  # noqa: F821
except BaseException:
    version = "unknown"


setup(
    name=name,
    author=author,
    author_email='dev@craban.de',
    url='https://github.com/AFM-analysis/afmformats',
    version=version,
    packages=find_packages(),
    package_dir={name: name},
    include_package_data=True,
    license="MIT",
    description=description,
    long_description=open('README.rst').read() if exists('README.rst') else '',
    install_requires=["h5py",
                      "igor",  # Asylum Research .ibw file format
                      "jprops",  # JPK file format
                      "numpy>=1.14.0",
                      ],
    python_requires='>=3.6, <4',
    keywords=["atomic force microscopy",
              "mechanical phenotyping",
              "tissue analysis"],
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Visualization',
        'Intended Audience :: Science/Research'
    ],
    platforms=['ALL'],
)
