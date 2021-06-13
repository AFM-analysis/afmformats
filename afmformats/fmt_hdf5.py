import functools
import pathlib

import h5py
import numpy as np

from .afm_data import column_dtypes, known_columns


__all__ = ["H5DictReader", "load_hdf5"]


class H5DictReader(object):
    def __init__(self, path_or_h5, enum_key):
        """Read-only HDF5-based dictionary for arrays

        Parameters
        ----------
        path_or_h5: str or pathlib.Path or h5py.Group
            Path to HDF5 file or an HDF5 group
        enum_key: str
            Name of the subgroup in `path_or_h5` that contains the data
            of the dictionary
        """
        if isinstance(path_or_h5, h5py.Group):
            # we are not responsible for the HDF5 file
            self.path = None
            self.h5 = path_or_h5
        else:
            # we are responsible for closing the HDF5 file
            self.path = path_or_h5
            self.h5 = None
        self.enum_key = enum_key
        self._columns = self.keys()

    def __contains__(self, key):
        return key in self._columns

    def __getitem__(self, key):
        if key not in known_columns:
            raise ValueError("Column '{}' is not documented!".format(key))
        elif key in self.keys():
            if self.path is not None:
                with h5py.File(self.path, "r") as h5:
                    val = np.asarray(h5[self.enum_key][key][:],
                                     dtype=column_dtypes[key])
            else:
                val = np.asarray(self.h5[self.enum_key][key][:],
                                 dtype=column_dtypes[key])
        else:
            raise KeyError("Column '{}' not in '{}/{}'".format(key, self.path,
                                                               self.enum_key))
        return val

    def __iter__(self):
        for kk in self._columns:
            yield kk

    @functools.lru_cache(maxsize=2)
    def keys(self):
        if self.path is not None:
            with h5py.File(self.path, "r") as h5:
                cols = sorted(h5[self.enum_key].keys())
        else:
            cols = sorted(self.h5[self.enum_key].keys())
        return cols


def load_hdf5(path_or_h5, callback=None, meta_override=None):
    """Loads HDF5 files as exported by afmformats

    The HDF5 format is self explanatory. The root attributes
    contain the version of afmformats used to create it. For each
    curve, one group is created, named according to "0", "1", ...
    "9", "10", "11", etc. The attributes of each group are key-value
    pairs defined in :const:`afmformats.meta.KEYS_VALID`. The group
    contains datasets named according to
    :const:`afmformats.afm_data.known_columns` and have the attribute
    "unit" with the corresponding value in
    :const:`afmformats.afm_data.column_units`.

    Parameters
    ----------
    path_or_h5: str or pathlib.Path or h5py.Group
        path to HDF5 file or an HDF5 group
    callback: callable
        function for progress tracking; must accept a float in
        [0, 1] as an argument.
    meta_override: dict
        if specified, contains key-value pairs of metadata that
        are used when loading the files
        (see :data:`afmformats.meta.META_FIELDS`)

    Notes
    -----
    In case `path_or_h5` is a h5py.Group object, the
    "path" metadata variable will always be set to the
    path of the original HDF5 file. Keep this in mind
    if you think about storing multiple datasets (each
    containing multiple curves) in one HDF5 file (bad idea).
    """
    if meta_override is None:
        meta_override = {}
    if isinstance(path_or_h5, h5py.Group):
        path = pathlib.Path(path_or_h5.file.filename)
        close = False
        h5 = path_or_h5
    else:
        path = pathlib.Path(path_or_h5)
        close = True
        h5 = h5py.File(path, "r")
    fdlist = []
    for enum_key in h5.keys():
        metadata = dict(h5[enum_key].attrs)
        metadata["path"] = path
        metadata["enum"] = int(enum_key)
        metadata.update(meta_override)
        data = H5DictReader(path_or_h5, enum_key=enum_key)
        fdlist.append({"data": data,
                       "metadata": metadata})
    if close:
        h5.close()
    if callback is not None:
        callback(1)
    return fdlist


recipe_hdf5 = {
    "descr": "HDF5-based",
    "loader": load_hdf5,
    "suffix": ".h5",
    "mode": "force-distance",
    "maker": "afmformats",
}
