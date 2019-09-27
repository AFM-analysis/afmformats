from os.path import dirname, exists, realpath
from setuptools import setup, Extension, find_packages
import sys

author = "Paul Müller"
authors = [author, "Shada Abuhattum"]
description = 'reading common AFM file formats'
name = 'afmformats'
year = "2019"


sys.path.insert(0, realpath(dirname(__file__))+"/"+name)
try:
    from _version import version  # @UnresolvedImport
except:
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
    install_requires=["jprops",
                      "lmfit==0.9.5",
                      "numpy>=1.14.0",
                      "pandas",
                      ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    python_requires='>=3.6, <4',
    keywords=["atomic force microscopy",
              "mechanical phenotyping",
              "tissue analysis"],
    classifiers= [
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Visualization',
        'Intended Audience :: Science/Research'
                 ],
    platforms=['ALL'],
    )

