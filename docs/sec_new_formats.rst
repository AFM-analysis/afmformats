=============================
Implementing new file formats
=============================

If you are interested in adding support for a new file format, please
`create a new issue <https://github.com/AFM-analysis/afmformats/issues/new>`_
to start a discussion. Please also attach a zip file with example data that
can later on be used during testing.

If you are familiar with GitHub, please create a pull request and make sure
that

- the file format reader is located in ``afmformats.formats.fmt_NAME``
  (it may be a directory or a file, depending on the complexity)
- the file format displays correctly `in the docs
  <https://afmformats.readthedocs.io/en/latest/sec_getting_started.html#supported-file-formats>`_
  and the docs compile without errors::

    cd docs
    pip install -r requirements.txt
    sphinx-build . _build
    # and open _build/index.html in a browser
- you updated the CHANGELOG
- your code is fully tested (create test functions in ``tests/test_fmt_NAME.py``)
  and all other tests pass (There are a few general tests that all file format
  readers must pass)::

    pip install pytest
    pytest tests


If you cannot or will not work with GitHub, you may paste your code in the
corresponding issue. If the file format is not too complicated, let's just
hope that things don't get messy.


Basic file format reader structure
==================================
The best way to understand how file formats work in afmformats is to take
a look at the `file formats implemented already
<https://github.com/AFM-analysis/afmformats/tree/master/afmformats/formats>`_.
For the sake of clarity, here is a :download:`file format reader template <data/fmt_template.py>`:

.. literalinclude:: data/fmt_template.py
   :language: python

A few notes:

- The ``recipe_myf`` contains the recipe for loading the file format into
  afmformats. It must be registered in ``afmformats/formats/__init__.py``.
- You may call the ``callback`` function with a floating point value
  between 0 and 1 (progress tracking) in-between of your loading steps if
  you expect that your file format reader is slow (e.g. several curves have
  to be loaded). This will give users of e.g. PyJibe visual feedback on
  how long they will have to wait.
- The ``meta_override`` dictionary is useful if you file format does not
  contain essential metadata such as spring constant or sensitivity.
  In such cases, you can raise an :class:`afmformats.errors.MissingMetaDataError`
  to signal PyJibe that it should ask the user for the missing metadata.
  For an example, please see the AFM workshop file format.


Optimizing data import
======================
In most cases, it is not neccessary to actually load the data from disk in the
`load_my_format` method, especially if you have to parse large binary blobs or
text files. In such cases, you can make use of the `lazy loaders
<https://en.wikipedia.org/wiki/Lazy_loading>`_ implemented in afmformats.
For metadata, you can use :class:`afmformats.meta.LazyMetaValue` and for
data columns, you can use :class:`afmformats.lazy_loader.LazyData`.
The JPK file reader makes heavy usage of those classes.
