import pathlib

import numpy as np

from .afm_data import AFMData
from .meta import MetaData


class AFMForceDistance(AFMData):
    """Base class for AFM force-distance data

    A force-distance data set consists of an approach and
    a retract curve.
    """

    def __init__(self, data, metadata, diskcache=False):
        """Initialization

        Parameters
        ----------
        data: dict-like

        """
        # convert meta data
        metadata_i = MetaData(metadata)
        # check data keys
        for cc in data:
            if cc not in known_columns:
                raise ValueError("Unknown feature name '{}'!".format(cc))
        self._path = pathlib.Path(metadata_i["path"])
        self._metadata = metadata_i
        self._enum = metadata_i["enum"]
        # raw data will not be touched
        self._raw_data = data
        self._data = {"segment": data["segment"]}
        if "index" not in self._raw_data:
            self._data["index"] = np.arange(len(data["segment"]))
        # TODO:
        # - implement caching (hdf5?)

    def __contains__(self, key):
        return self._data.__contains__(key) or self._raw_data.__contains__(key)

    def __getitem__(self, key):
        if key in self._data:
            data = self._data[key]
        elif key in self._raw_data:
            data = self._raw_data[key].copy()
        else:
            raise KeyError("Unknown column '{}'!".format(key))
        if hasattr(data, "values"):
            # pandas
            data = data.values
        return data

    def __len__(self):
        return len(self._data["segment"])

    def __setitem__(self, key, values):
        if len(values) != len(self):
            raise ValueError(
                "Cannot set data of length '{}' ".format(len(values))
                + "for AFMForceDistance of length '{}'!".format(len(self)))
        # do not touch raw data
        self._data[key] = values

    @property
    def appr(self):
        """Dictionary-like interface to the approach segment"""
        return Segment(self._raw_data, self._data, which="approach")

    @property
    def columns(self):
        """Available data columns"""
        raw = self._raw_data.keys()
        new = self._data.keys()
        return sorted(set(raw) | set(new))

    @property
    def enum(self):
        """Unique index of `self` in `self.path`"""
        return self._enum

    @property
    def metadata(self):
        """Unique index of `self` in `self.path`"""
        return MetaData(self._metadata.copy())

    @property
    def mode(self):
        """Imaging modality"""
        return "force-distance"

    @property
    def path(self):
        """Path to the measurement file"""
        return self._path

    @property
    def retr(self):
        """Dictionary-like interface to the retract segment"""
        return Segment(self._raw_data, self._data, which="retract")

    def export(self, path):
        """Export all columns to a tab-separated value file"""
        path = pathlib.Path(path)
        cols = self.columns
        end = "\r\n"
        # get all data (faster than doing it every time for every row)
        data = {}
        for cc in cols:
            data[cc] = self[cc]

        with path.open("w") as fd:
            # header
            fd.write("#" + "\t".join(cols) + end)
            # rows
            for ii in range(len(self)):
                items = []
                for cc in cols:
                    if cc in column_dtypes and column_dtypes[cc] == bool:
                        items.append("{}".format(data[cc][ii]))
                    else:
                        items.append("{:.8e}".format(data[cc][ii]))
                fd.write("\t".join(items) + end)


class Segment(object):
    """Simple wrapper around dict-like `data` to expose a single segment"""

    def __init__(self, raw_data, data, which="approach"):
        if which not in ["approach", "retract"]:
            raise ValueError("`which` must be 'approach' or 'retract', "
                             + "got '{}'!".format(which))
        #: The segment type (approach or retract)
        self.which = which
        if which == "approach":
            self.idx = False
        else:
            self.idx = True
        self.raw_data = raw_data
        self.data = data

    def __getitem__(self, key):
        used = self.data["segment"] == self.idx
        if key in self.data:
            return self.data[key][used]
        elif key in self.raw_data:
            return self.raw_data[key][used].copy()
        else:
            raise KeyError("Undefined feature '{}'!".format(key))


#: Data types of all known columns (all other columns are assumed to be float)
column_dtypes = {
    "force": float,
    "height (measured)": float,
    "segment": bool,
    "time": float,
    "tip position": float,
}

#: Known data columns
known_columns = sorted(column_dtypes.keys())
