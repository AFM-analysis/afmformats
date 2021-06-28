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