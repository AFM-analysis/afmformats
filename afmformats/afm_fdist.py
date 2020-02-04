from .afm_data import AFMData


__all__ = ["AFMForceDistance", "Segment"]


class AFMForceDistance(AFMData):
    """Base class for AFM force-distance data

    A force-distance dataset consists of an approach and
    a retract curve.
    """

    def __repr__(self):
        repre = "<Force-Distance Data '{}'[{}] at {}>".format(
            self.path, self.enum, hex(id(self)))
        return repre

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
    def mode(self):
        """Imaging modality"""
        return "force-distance"

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
