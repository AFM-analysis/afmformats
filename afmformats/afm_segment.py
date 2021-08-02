__all__ = ["AFMSegment"]


class AFMSegment(object):
    """Simple wrapper around dict-like `data` to expose a single segment

    This class also caches the segment indices.
    """
    def __init__(self, raw_data, data, segment):
        #: The segment type (approach, intermediate, or retract)
        self.segment = segment
        self.raw_data = raw_data
        self.data = data

        self._raw_segment_indices = None
        self._user_segment_indices = None

    def __getitem__(self, key):
        """Access column data of the segment"""
        if key in self.data:
            return self.data[key][self.segment_indices]
        elif key in self.raw_data:
            return self.raw_data[key][self.segment_indices].copy()
        else:
            raise KeyError("Undefined feature '{}'!".format(key))

    @property
    def segment_indices(self):
        """boolean array of segment indices"""
        if "segment" in self.data:  # data takes precedence (user-edited)
            if self._user_segment_indices is None:
                self._user_segment_indices = \
                    self.data["segment"] == self.segment
            indices = self._user_segment_indices
        elif "segment" in self.raw_data:
            # indices from raw data can safely be cached (will not change)
            if self._raw_segment_indices is None:
                self._raw_segment_indices = \
                    self.raw_data["segment"] == self.segment
            indices = self._raw_segment_indices
        else:
            raise ValueError("Could not identify segment data!")
        return indices

    def clear_cache(self):
        """Invalidates the segment indices corresponding to `self.data`"""
        self._user_segment_indices = None
