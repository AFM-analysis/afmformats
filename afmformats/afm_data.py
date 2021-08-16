import abc
import io
import json
import pathlib
import warnings

import h5py
import numpy as np

from ._version import version
from .meta import MetaData


__all__ = ["AFMData", "column_dtypes", "column_units", "known_columns"]


class AFMData(abc.ABC):
    """General base class for AFM data"""

    def __init__(self, data, metadata, diskcache=False):
        """Initialization

        Parameters
        ----------
        data: dict-like
            Experimental data
        metadata: dict
            Metadata
        diskcache: bool
            TODO
        """
        # convert meta data
        metadata_i = MetaData(metadata)
        # check data keys
        for cc in data:
            if cc not in known_columns:
                raise ValueError("Unknown column name '{}'!".format(cc))
        self._path = pathlib.Path(metadata_i["path"])
        self._metadata = metadata_i
        self._enum = metadata_i["enum"]
        # raw data will not be touched
        self._raw_data = data
        self._data = {}

    def __contains__(self, key):
        return self._data.__contains__(key) or self._raw_data.__contains__(key)

    def __getitem__(self, key):
        if key in self._data:
            data = self._data[key]
        elif key in self._raw_data:
            data = self._raw_data[key].copy()
        elif key == "index":
            return np.arange(len(self))
        else:
            raise KeyError("Column '{}' not defined!".format(key))
        return data

    def __len__(self):
        # If you are here, you might have asked yourself why
        # loading your data takes so long. You have tried
        # lazy-loading and there shouldn't be a reason why
        # it is sooo slow! Except there is, because we need
        # the size of the dataset - and if that is not in the
        # metadata, then we just take the length of the first
        # data column as a workaround (which takes time).
        if "point count" not in self._metadata:
            k0 = list(self._raw_data.keys())[0]
            length = len(self[k0])
        else:
            length = self._metadata["point count"]
        return length

    def __setitem__(self, key, values):
        """Set column data"""
        if len(values) != len(self):
            raise ValueError(
                f"Cannot set data '{key}' of length '{len(values)}' "
                + f"for AFMForceDistance of length '{len(self)}'!")
        # do not touch raw data
        self._data[key] = values

    def __str__(self):
        strre = "{} '{}'[{}]".format(
            self.__class__.__name__, self.path, self.enum)
        return strre

    def __repr__(self):
        repre = "<{} '{}'[{}] at {}>".format(
            self.__class__.__name__, self.path, self.enum, hex(id(self)))
        return repre

    @property
    def columns(self):
        """Available data columns"""
        raw = self._raw_data.keys()
        new = self._data.keys()
        return sorted(set(raw) | set(new))

    @property
    def columns_innate(self):
        """Data columns available only in the original data file"""
        return sorted(self._raw_data.keys())

    @property
    def enum(self):
        """Unique index of `self` in `self.path`

        Indexing starts at "0"
        """
        return self._enum

    @property
    def metadata(self):
        """Unique index of `self` in `self.path`"""
        return MetaData(self._metadata.copy())

    @property
    @abc.abstractmethod
    def modality(self):
        """Imaging modality (e.g. force-distance)"""

    @property
    def path(self):
        """Path to the measurement file"""
        return self._path

    def _export_hdf5(self, h5group, metadata_dict=None):
        """Export data to the HDF5 file format

        Parameters
        ----------
        h5group: h5py.Group or h5py.File
            Destination group
        metadata_dict: dict
            Key-value pairs for the metadata that should be exported
            (will be stored in the group attributes)
        """
        # set the software and its version
        if metadata_dict is None:
            metadata_dict = {}
        h5group.attrs["software"] = "afmformats"
        h5group.attrs["software version"] = version
        enum_key = str(self.enum)
        if enum_key in h5group:
            # random fill-mode (get the next free enum key)
            ii = 0
            while True:
                enum_key = str(ii)
                if enum_key not in h5group:
                    break
                ii += 1
        metadata_dict["enum"] = int(enum_key)
        subgroup = h5group.create_group(enum_key)
        for col in self.columns:
            if col == "segment":
                ds = subgroup.create_dataset(name=col,
                                             data=np.asarray(self[col],
                                                             dtype=np.uint8),
                                             compression="gzip",
                                             fletcher32=True)
            elif col == "index":
                # do not store index column
                continue
            else:
                ds = subgroup.create_dataset(name=col,
                                             data=self[col],
                                             compression="gzip",
                                             fletcher32=True)
            ds.attrs["unit"] = column_units[col]
        for kk in metadata_dict:
            if kk == "path":
                subgroup.attrs["path"] = str(metadata_dict["path"])
            else:
                subgroup.attrs[kk] = metadata_dict[kk]

    def _export_tab(self, fd, metadata_dict=None):
        """Export data to a tab separated values file

        Parameters
        ----------
        fd: io.IOBase
            File opened in "w" mode
        metadata_dict: dict
            Key-value pairs for the metadata that should be exported
            (will be stored in the group attributes)
        """
        if metadata_dict is None:
            metadata_dict = {}
        fd.write("# afmformats {}\r\n".format(version))
        fd.write("#\r\n")
        if metadata_dict:
            # write metadata
            dump = json.dumps(metadata_dict, sort_keys=True, indent=2,
                              default=json_path_serializer)
            fd.write("# BEGIN METADATA\r\n")
            for dl in dump.split("\n"):
                fd.write("# " + dl + "\r\n")
            fd.write("# END METADATA\r\n")
            fd.write("#\r\n")
        # get all data (faster than doing it every time for every row)
        data = {}
        for cc in self.columns:
            data[cc] = self[cc]
        # header
        fd.write("# " + "\t".join(self.columns) + "\r\n")
        # rows
        for ii in range(len(self)):
            items = []
            for cc in self.columns:
                items.append("{:.8g}".format(data[cc][ii]))
            fd.write("\t".join(items) + "\r\n")

    def export(self, *args, **kwargs):
        warnings.warn("Pleas use `export_data` for data export!",
                      DeprecationWarning)
        return self.export_data(*args, **kwargs)

    def export_data(self, out, metadata=True, fmt="tab"):
        """Export all data columns to a file

        Parameters
        ----------
        out: str, pathlib.Path, writable io.IOBase, or h5py.Group
            Output path, open file, or h5py object
        metadata: bool or list
            If True, all available metadata are stored. If False,
            no metadata are stored. If a list, only the given
            metadata keys are stored.
        fmt: str
            "tab" for the tab separated values format and "hdf5" / "h5"
            for the HDF5 file format

        Notes
        -----
        - If you wish to append HDF5 data to an existing file, please
          open the file first and call this function with the h5py.File
          object, i.e.

          .. code:: python

              with h5py.File(path, "a") as h5:
                  fdist.export(out=h5, fmt="hdf5")

          Otherwise the file will be overridden.
        - The column "index" is not exported in the HDF5 file
          format
        """
        if isinstance(metadata, (list, tuple)):
            # list of keys
            metadata_dict = {}
            for key in metadata:
                metadata_dict[key] = self.metadata[key]
        elif isinstance(metadata, bool) and metadata:
            # all metadata
            metadata_dict = self.metadata
        else:
            raise ValueError("Metadata must be list, tuple, or bool, got "
                             f"'{metadata}' of type '{type(metadata)}'!")

        if fmt == "tab":
            if isinstance(out, (pathlib.Path, str)):
                fd = pathlib.Path(out).open("w")
                close = True
            elif isinstance(out, io.IOBase):
                fd = out
                close = False
            else:
                raise ValueError("Unexpected object class for 'out': "
                                 + "'{}' for format 'tab'!".format(
                                     out.__class__))
            self._export_tab(fd, metadata_dict=metadata_dict)
            if close:
                fd.close()
        elif fmt in ["hdf5", "h5"]:
            if isinstance(out, (pathlib.Path, str)):
                # overrides always
                h5 = h5py.File(out, "w")
                close = True
            elif isinstance(out, h5py.Group):
                h5 = out
                close = False
            else:
                raise ValueError("Unexpected object class for 'out': "
                                 + "'{}' for format 'hdf5'!".format(
                                     out.__class__))
            self._export_hdf5(h5group=h5, metadata_dict=metadata_dict)
            if close:
                h5.close()
        else:
            raise ValueError("Unexpected string for 'fmt': {}".format(fmt))

    def reset_data(self):
        """Resets all data to the state they were after loading

        Internally, only `self._data` is `clear`ed, which means
        that all calls to `__getitem__` fall-back to `self._raw_data`.
        """
        self._data.clear()


def json_path_serializer(obj):
    """Used to convert pathlib.Path to str in metadata"""
    if isinstance(obj, pathlib.Path):
        return str(obj)
    else:
        raise TypeError(f"TypeError: Object of type {obj.__class__} "
                        + "is not JSON serializable")


#: Data types of all known columns (all other columns are assumed to be float)
column_dtypes = {
    "force": float,
    "height (measured)": float,
    "height (piezo)": float,
    "index": int,
    "segment": np.uint8,
    "time": float,
    "tip position": float,
}

#: Units of all known columns
column_units = {
    "force": "N",
    "height (measured)": "m",
    "height (piezo)": "m",
    "index": "",
    "segment": "",
    "time": "s",
    "tip position": "m",
}

#: Known data columns
known_columns = sorted(column_dtypes.keys())
