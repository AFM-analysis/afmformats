__all__ = ["AFMSegment"]


class AFMSegment(object):
    """Simple wrapper around dict-like `data` to expose a single segment

    This class also caches the segment indices.
    """
    def __init__(self, raw_data, data, segment):
        """New Segment data

        Parameters
        ----------
        raw_data: dict
            dictionary containing valid column names as keys and
            1d ndarrays as values; this is raw data (e.g. from the
            measurement file) that may be lazily-loaded
        data: dict
            same as raw_data, but in this case the data are already
            in memory; we distinguish between raw_data and data so
            that we know where the data came from (e.g. there might
            be "tip poisition" in both dictionaries, but we only
            always use (and override) the "tip position" in `data`.
            We never touch `raw_data`.
        """
        #: The segment type (approach, intermediate, or retract)
        self.segment = segment
        self._raw_data = raw_data
        self._data = data

        self._raw_segment_indices = None
        self._user_segment_indices = None

    def __getitem__(self, key):
        """Access column data of the segment"""
        if key in self._data:
            return self._data[key][self.segment_indices]
        elif key in self._raw_data:
            return self._raw_data[key][self.segment_indices].copy()
        else:
            raise KeyError("Undefined column '{}'!".format(key))

    def __setitem__(self, key, data):
        """Set column data of the segment"""
        if key not in self._data and key not in self._raw_data:
            raise KeyError("Undefined column '{}'!".format(key))
        self._data[key][self.segment_indices] = data

    @property
    def segment_indices(self):
        """boolean array of segment indices"""
        if "segment" in self._data:  # data takes precedence (user-edited)
            if self._user_segment_indices is None:
                self._user_segment_indices = \
                    self._data["segment"] == self.segment
            indices = self._user_segment_indices
        elif "segment" in self._raw_data:
            # indices from raw data can safely be cached (will not change)
            if self._raw_segment_indices is None:
                self._raw_segment_indices = \
                    self._raw_data["segment"] == self.segment
            indices = self._raw_segment_indices
        else:
            raise ValueError("Could not identify segment data!")
        return indices

    def clear_cache(self):
        """Invalidates the segment indices corresponding to `self.data`"""
        self._user_segment_indices = None
