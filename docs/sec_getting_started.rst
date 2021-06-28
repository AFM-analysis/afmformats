===============
Getting started
===============


Installation
============
To install afmformats, use one of the following methods
(the package dependencies will be installed automatically):

* from `PyPI <https://pypi.python.org/pypi/afmformats>`_:
    ``pip install afmformats``
* from `sources <https://github.com/AFM-Analysus/afmformats>`_:
    ``pip install -e .``


Basic Usage
===========

.. ipython::

    In [1]: import afmformats

    In [2]: dslist = afmformats.load_data("data/force-save-example.jpk-force")

    # dslist is a list of force-distance curves
    In [3]: dslist

    # available data columns of the first curve
    In [4]: dslist[0].columns

    In [5]: dslist[0]["force"]


.. _supported_formats:

Supported file formats
======================
All supported file formats are listed in the table below.
If you are interested in other file formats, please
`create a new issue <https://github.com/AFM-analysis/afmformats/issues/new>`_.

.. afmformats_file_formats::


Notes
=====
Afmformats is a base module for loading experimental data.
You might want to use `nanite <https://nanite.readthedocs.io/>`_ or
`PyJibe <https://pyjibe.readthedocs.io/>`_ for higher-level functionalities.