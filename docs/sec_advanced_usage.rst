.. _sec_av:

==============
Advanced Usage
==============


Grouping AFM data
=================
AFM data can be organized in an :class:`afmformats.AFMGroup
<afmformats.afm_group.AFMGroup>` which comes with a few user-convenient
functionalities:

.. ipython::

    In [1]: import afmformats

    In [2]: group = afmformats.AFMGroup("data/force-map2x2-example.jpk-force-map")

    # group contains all curves in the data file
    In [3]: print(group)

    # you may add other data files to groups
    In [4]: group += afmformats.load_data("data/force-save-example.jpk-force")

    In [5]: print(group)

    # You can also extract a subgroup that matches a certin path
    In [6]: subgroup = group.subgroup_with_path("data/force-map2x2-example.jpk-force-map")

    In [7]: print(subgroup)


Logging (for developers)
========================
``afmformats`` now has a simple logging system. When loading data in a script
or in the console, debug-level logs will be written to `afmformats.log` in
your machine's temp folder. Additionally, when debugging file loading in a
local script, the ``afmformats.log`` debug log will output to the terminal if
you call ``afmformats.configure_console_logging()``:

.. code-block:: python

    import pathlib
    import afmformats

    data_path = pathlib.Path("tests/data")

    afmformats.configure_console_logging()

    afmformats.load_data(data_path / "fmt-hdf5-fd_version_0.13.3.h5")

Output of the above script:

.. code-block::

    DEBUG:afmformats.formats:Loaded 1 dataset(s) from '...\afmformats\tests\data\fmt-hdf5-fd_version_0.13.3.h5' using 'HDF5-based'

    Process finished with exit code 0
