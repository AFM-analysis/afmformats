import abc
import copy
import io
import json
import pathlib

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
        self._data = {"segment": data["segment"]}
        if "index" not in self._raw_data:
            self._data["index"] = np.arange(len(data["segment"]))

    def __contains__(self, key):
        return self._data.__contains__(key) or self._raw_data.__contains__(key)

    def __getitem__(self, key):
        if key in self._data:
            data = self._data[key]
        elif key in self._raw_data:
            data = self._raw_data[key].copy()
        else:
            raise KeyError("Column '{}' not defined!".format(key))
        return data

    def __len__(self):
        return len(self._data["segment"])

    @abc.abstractmethod
    def __repr__(self):
        """Meaningful repr string"""

    @property
    def columns(self):
        """Available data columns"""
        raw = self._raw_data.keys()
        new = self._data.keys()
        return sorted(set(raw) | set(new))

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
    def mode(self):
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
            # convert path to string for export (json)
            if "path" in metadata_dict:
                metadata_dict = copy.deepcopy(metadata_dict)
                metadata_dict["path"] = str(metadata_dict["path"])
            # write metadata
            dump = json.dumps(metadata_dict, sort_keys=True, indent=2)
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
                if cc in column_dtypes and column_dtypes[cc] == bool:
                    items.append("{}".format(data[cc][ii]))
                else:
                    items.append("{:.8g}".format(data[cc][ii]))
            fd.write("\t".join(items) + "\r\n")

    def export(self, out, metadata=True, fmt="tab"):
        """Export all columns to a file

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
            metadata_dict = {}
            for key in metadata:
                metadata_dict[key] = self.metadata[key]
        elif isinstance(metadata, bool) and metadata:
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


#: Data types of all known columns (all other columns are assumed to be float)
column_dtypes = {
    "force": float,
    "height (measured)": float,
    "height (piezo)": float,
    "index": int,
    "segment": bool,
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
