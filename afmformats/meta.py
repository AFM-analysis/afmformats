import pathlib

import numpy as np

from .parse_funcs import fint, vd_str_in


__all__ = ["IMAGING_MODALITIES", "META_FIELDS", "DEF_ALL", "KEYS_VALID",
           "MetaDataMissingError", "LazyMetaValue", "MetaData", "parse_time"]


#: supported imaging modalities
IMAGING_MODALITIES = [
    # creep-compliance (constant force)
    "creep-compliance",
    # force-distance (indent until setpoint and retract)
    "force-distance",
    # stress-relaxation (constant indentation)
    "stress-relaxation",
    ]

#: Compendium of all allowed meta data keys, sorted by topic, and
#: including units and validation methods
META_FIELDS = {
    # AFM acquisition settings
    "acquisition": {
        "feedback mode": ["Feedback mode", "", vd_str_in([
            # JPK contact mode
            "contact",
            # From the NanoWizard User Manual (v. 4.2) sec. 5.7:
            # Force modulation mode is a mixture between contact mode and
            # intermittent mode and "can be thought of as a kind of contact
            # mode with an added vibration on the cantilever".
            "force-modulation",
        ])],
        "imaging mode": ["Imaging modality", "",
                         vd_str_in(IMAGING_MODALITIES)],
        "sensitivity": ["Sensitivity", "m/V", float],
        "spring constant": ["Cantilever spring constant", "N/m", float],
    },
    # dataset parameters
    "dataset": {
        "duration": ["Duration", "s", float],
        "duration approach": ["Duration of approach segment", "s", float],
        "duration retract": ["Duration of retract segment", "s", float],
        "enum": ["Dataset index within the experiment", "", fint],
        "point count": ["Size of the dataset in points", "", fint],
        "rate approach": ["Sampling rate of approach segment", "Hz", float],
        "rate retract": ["Sampling rate of retract segment", "Hz", float],
        "segment count": ["Number of segments", "", fint],
        "setpoint": ["Target indentation force", "N", float],
        "speed approach": ["Piezo speed of approach segment", "m/s", float],
        "speed retract": ["Piezo speed of retract segment", "m/s", float],
        "z range": ["Axial piezo range", "m", float],
    },
    # parameters specific for creep-compliance
    "dataset-mod creep-compliance": {
        "duration intermediate": ["Duration of intermediate segment",
                                  "s", float],
    },
    # QMap related dataset metadata
    "qmap": {
        "grid center x": ["Horizontal center of grid", "m", float],
        "grid center y": ["Vertical center of grid", "m", float],
        "grid index x": ["Horizontal grid position index", "", fint],
        "grid index y": ["Vertical grid position index", "", fint],
        "grid shape x": ["Horizontal grid shape", "px", fint],
        "grid shape y": ["Vertical grid shape", "px", fint],
        # The grid size is the actual size when you include the
        # boundary of the image (i.e. (grid_shape + 1) * pixel_size).
        "grid size x": ["Horizontal grid image size", "m", float],
        "grid size y": ["Vertical grid image size", "m", float],
        "position x": ["Horizontal position", "m", float],
        "position y": ["Vertical position", "m", float],
    },
    # AFM setup
    "setup": {
        "instrument": ["Instrument", "", str],
        "software": ["Acquisition software", "", str],
        "software version": ["Acquisition software version", "", str],
    },
    # storage data
    "storage": {
        "curve id": ["Curve identifier", "", str],
        "date": ["Recording date", "", str],  # YYYY-MM-DD
        "format": ["File format", "", str],
        "path": ["Path", "", pathlib.Path],
        "session id": ["Dataset identifier", "", str],
        "time": ["Recording time", "", str],  # HH:MM:SS.S
    },
}


#: A dictionary for all metadata definitions
DEF_ALL = {}
for _sec in META_FIELDS:
    for _key in META_FIELDS[_sec]:
        DEF_ALL[_key] = META_FIELDS[_sec][_key]

#: List of all valid meta data keys
KEYS_VALID = sorted(DEF_ALL.keys())


class MetaDataMissingError(BaseException):
    """Raised when meta data is missing"""
    pass


class LazyMetaValue:
    """A metadata value that is evaluated lazily in :class:`MetaData`"""
    def __init__(self, func, *args, **kwargs):
        """

        Example usage::

           meta = afmformats.meta.MetaData
           meta["z range"] = afmformats.meta.LazyMetaValue(
                np.ptp,
                np.arange(10))

        Parameters
        ----------
        func: callable
            Function to call to get the metadata value
        args:
            arguments to ``func``
        kwargs:
            Keyword arguments to ``func``
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.value = None

    def __call__(self):
        if self.value is None:
            # When metadata is copied, LazyMetaValue is copied along with
            # it. If in the copy, this function here is called, then we
            # store it in self.value, so it does not have to be recomputed
            # in another copy.
            self.value = self.func(*self.args, **self.kwargs)
        return self.value


class MetaData(dict):
    """Management of meta data variables

    Valid key names are defined in :const:`afmformats.meta.KEYS_VALID`.
    """
    valid_keys = KEYS_VALID

    def __init__(self, *args, **kwargs):
        # do not init with args/kwargs
        super(MetaData, self).__init__()
        # instead, make sure everything goes through __set__
        self.update(*args, **kwargs)
        # check for invalid keys
        for key in self:
            if key not in self.valid_keys:
                raise KeyError("Unknown metadata key: '{}'".format(key))

    def __copy__(self):
        """Create a copy of the metadata

        Returns
        -------
        mdc: MetaData
            Copy of the MetaData class (LazyMetaValue not copied)
        """
        cls = MetaData()
        for key in self:
            # This will just pass the LazyMetaValue instance and
            # not create a copy of it.
            cls[key] = super(MetaData, self).__getitem__(key)
        return cls

    def __deepcopy__(self, memo):
        # Since MetaData is not a nested dictionary, we just do a copy.
        # And LazyMetaValue should not be copied.
        result = self.__copy__()
        memo[id(self)] = result
        return result

    def __setitem__(self, key, value):
        """Set a metadata key

        The key must be a valid key defined in `self.valid_keys`
        (defaults to :const:`afmformats.meta.KEYS_VALID`).

        The "time" key is converted using :func:`parse_time`.
        NaN values are silently ignored.
        """
        if key not in self.valid_keys:
            raise KeyError("Unknown metadata key: '{}'".format(key))
        elif key == "time":
            value = parse_time(value)
        elif key == "imaging mode" and "segment count" not in self:
            if value == "force-distance":
                self["segment count"] = 2
            elif value in ["creep-compliance", "stress-relaxation"]:
                self["segment count"] = 3
            else:
                # Dear future self...
                raise ValueError(f"Please add '{value}' to this case!")
        if isinstance(value, float) and np.isnan(value):
            # nan values are ignored
            return
        if not isinstance(value, LazyMetaValue):
            # parse the value
            value = DEF_ALL[key][2](value)
        super(MetaData, self).__setitem__(key, value)
        self._autocomplete_grid_metadata()

    def __getitem__(self, key):
        if key == "curve id":
            return self._get_curve_id()
        elif key == "session id":
            return self._get_session_id()
        elif key not in self and key in self.valid_keys:
            msg = "No meta data was defined for '{}'! ".format(key) \
                  + "Please make sure you passed the dictionary `metadata` " \
                  + "when you loaded your data."
            raise MetaDataMissingError(msg)
        elif key not in self:
            msg = "Unknown meta key: '{}'!".format(key)
            raise KeyError(msg)

        value = super(MetaData, self).__getitem__(key)

        if isinstance(value, LazyMetaValue):
            # Evaluate LazyMetaValue and assign value to self
            value = value()
            # parse the value
            value = DEF_ALL[key][2](value)
            super(MetaData, self).__setitem__(key, value)
        return value

    def _autocomplete_grid_metadata(self):
        """Compute missing grid metadata in-place

        - supplements "grid index x" and "grid index y" if possible
        """
        md = self
        for ax in ["x", "y"]:
            if (f"grid index {ax}" not in self
                and f"grid center {ax}" in self
                and f"grid shape {ax}" in self
                and f"grid size {ax}" in self
                    and f"position {ax}" in self):
                idx = self._convert_position_to_index(
                    pos_m=md[f"position {ax}"],
                    size_m=md[f"grid size {ax}"],
                    center_m=md[f"grid center {ax}"],
                    size_px=md[f"grid shape {ax}"])
                super(MetaData, self).__setitem__(f"grid index {ax}", idx)

    @staticmethod
    def _convert_position_to_index(pos_m, size_m, center_m, size_px):
        """Convert qmap positions from [m] to array coordinates in [px]

        Parameters
        ----------
        pos_m: float
            positions [m]
        size_m: float
            grid size [m]
        center_m: float
            grid center position [m]
        size_px: int
            grid size [px]

        Returns
        -------
        pos_px: int
            index position of `pos_m`
        """
        if size_px != int(size_px):
            raise ValueError(
                "`size_px` must be integer, got {}!".format(size_px))
        size_px = int(size_px)
        s1 = center_m - size_m / 2
        s2 = center_m + size_m / 2

        x, dx = np.linspace(s1, s2, size_px, endpoint=False, retstep=True)
        x += dx / 2

        xpx = np.nanargmin(np.abs(x - pos_m))
        return xpx

    def _get_curve_id(self):
        # already set?
        thisid = super(MetaData, self).get("curve id")
        # compute using session_id
        if not thisid and "enum" in self:
            thisid = self._get_session_id() + "_{}".format(self["enum"])
        # not available
        if not thisid:
            raise MetaDataMissingError("Key 'curve id' not set!")
        return thisid

    def _get_session_id(self):
        # already set?
        thisid = super(MetaData, self).get("session id")
        # compute using date/time
        if not thisid:
            idlist = [self.get("date", ""),
                      self.get("time", "")]
            thisid = "_".join([it for it in idlist if it])
        # not available
        if not thisid:
            raise MetaDataMissingError("Key 'session id' not set!")
        return thisid

    def as_dict(self):
        """Convert to real dictionary

        This is needed e.g. for `self.items` such that `json.dump`
        works in combination with `LazyMetaValue` (which is not
        JSON serializable)
        """
        realdict = {}
        for key in self:
            realdict[key] = self[key]
        return realdict

    def copy(self):
        """Create a copy of the metadata

        Returns
        -------
        mdc: MetaData
            Copy of the MetaData class (LazyMetaValue not copied)
        """
        return self.__copy__()

    def get(self, key, default=None):
        if key in self:
            return self[key]
        else:
            return default

    def get_summary(self):
        """Convenience function returning the meta data summary

        Returns a dict of dicts with keys matching the DEF_* dicts.
        Unset values are returned as `np.nan`.
        """
        summary = {}
        for sec in META_FIELDS:
            if sec.startswith("dataset-mod"):
                if self["imaging mode"] not in sec:
                    # Ignore metadata that do not belong to the current
                    # imaging modality.
                    continue
                else:
                    # Write "dataset-mod" metadata to the "dataset" section
                    sum_sec = "dataset"
            else:
                sum_sec = sec
            summary.setdefault(sum_sec, {})
            for key in META_FIELDS[sec]:
                summary[sum_sec][key] = self.get(key, np.nan)
        return summary

    def items(self):
        return self.as_dict().items()

    def update(self, *args, **kwargs):
        # make sure everything goes through __set__
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    def values(self):
        return self.as_dict().values()


def parse_time(value):
    """Convert a time string to "HH:MM:SS.S"

    - leading zeros are added where necessary
    - trailing zeros after "." are stripped
    - trailing "." is stripped

    e.g.

    - "6:15:22 PM" -> "18:15:22"
    - "6:15:22.00 AM" -> "06:15:22"
    - "6:02:22.010 AM" -> "06:02:22.01"
    """
    # fix AM/PM
    if value.count(" "):
        time, ap = value.split()
        if ap == "PM":  # convert to 24h
            timetup = time.split(":")
            timetup[0] = str(int(timetup[0]) + 12)
            time = ":".join(timetup)
    else:
        time = value
    # convert to time with leading zeros and stripped subseconds
    hh, mm, ss = time.split(":")
    if ss.count("."):
        ss0, ss1 = ss.split(".")
        ss1 = ("." + ss1).rstrip(".0")
    else:
        ss0 = ss
        ss1 = ""

    # strip escape characters.
    # See https://github.com/AFM-analysis/afmformats/issues/43
    hh = hh.strip("\\")
    mm = mm.strip("\\")
    
    newvalue = ":".join(["{:02d}".format(int(hh)),
                         "{:02d}".format(int(mm)),
                         "{:02d}".format(int(ss0)) + ss1
                         ])
    return newvalue
