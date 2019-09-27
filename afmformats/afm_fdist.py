import pathlib

import numpy as np

from .afm_data import AFMData
from .metadata import MetaData


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
        for key in data:
            if key not in valid_features:
                raise ValueError("Unknown feature name '{}'!".format(key))
        self._path = pathlib.Path(metadata_i["path"])
        self._metadata = metadata_i
        self._index = metadata_i["index"]
        # raw data will not be touched
        self._raw_data = data
        self._data = {"segment": data["segment"]}
        if "index" not in self._raw_data:
            self._data["index"] = np.arange(len(data["segment"]))
        # TODO:
        # - implement caching (hdf5?)

    def __getitem__(self, key):
        if key in self._data:
            return self._data[key]
        elif key in self._raw_data:
            return self._raw_data[key].copy()
        else:
            raise KeyError("Unknown feature '{}'!".format(key))

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
    def index(self):
        """Unique index of `self` in `self.path`"""
        return self._index

    @property
    def metadata(self):
        """Unique index of `self` in `self.path`"""
        return self._metadata.copy()

    @property
    def path(self):
        """Path to the measurement file"""
        return self._path

    @property
    def retr(self):
        """Dictionary-like interface to the retract segment"""
        return Segment(self._raw_data, self._data, which="retract")


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


valid_features = [
    "force",
    "height (measured)",
    "segment",
    "time",
    "tip position",
]
