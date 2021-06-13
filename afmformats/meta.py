import pathlib

import numpy as np

from .parse_funcs import fint, vd_str_in


__all__ = ["META_FIELDS", "DEF_ALL", "KEYS_VALID", "MetaDataMissingError",
           "MetaData", "parse_time"]


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
        "imaging mode": ["Imaging modality", "", vd_str_in([
            # force-distance measurements
            "force-distance",
        ])],
        "rate approach": ["Sampling rate (approach)", "Hz", float],
        "rate retract": ["Sampling rate (retract)", "Hz", float],
        "sensitivity": ["Sensitivity", "m/V", float],
        "setpoint": ["Active feedback loop setpoint", "N", float],
        "spring constant": ["Cantilever spring constant", "N/m", float],
    },
    # dataset parameters
    "dataset": {
        "duration": ["Duration", "s", float],
        "enum": ["Dataset index within the experiment", "", fint],
        "point count": ["Size of the dataset in points", "", fint],
        "speed approach": ["Piezo speed (approach)", "m/s", float],
        "speed retract": ["Piezo speed (retract)", "m/s", float],
        "z range": ["Axial piezo range", "m", float],
    },
    # QMap related dataset metadata
    "qmap": {
        "grid center x": ["Horizontal center of grid", "m", float],
        "grid center y": ["Vertical center of grid", "m", float],
        "grid index x": ["Horizontal grid position index", "", fint],
        "grid index y": ["Vertical grid position index", "", fint],
        "grid shape x": ["Horizontal grid shape", "px", fint],
        "grid shape y": ["Vertical grid shape", "px", fint],
        "grid size x": ["Horizontal grid size", "m", float],
        "grid size y": ["Vertical grid size", "m", float],
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
        if isinstance(value, float) and np.isnan(value):
            # nan values are ignored
            return
        super(MetaData, self).__setitem__(key, value)

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
        return super(MetaData, self).__getitem__(key)

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

    def get_summary(self):
        """Convenience function returning the meta data summary

        Returns a dict of dicts with keys matching the DEF_* dicts.
        Unset values are returned as `np.nan`.
        """
        summary = {}
        for sec in META_FIELDS:
            summary[sec] = {}
            for key in META_FIELDS[sec]:
                summary[sec][key] = self.get(key, np.nan)
        return summary

    def update(self, *args, **kwargs):
        # make sure everything goes through __set__
        for k, v in dict(*args, **kwargs).items():
            self[k] = v


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
    newvalue = ":".join(["{:02d}".format(int(hh)),
                         "{:02d}".format(int(mm)),
                         "{:02d}".format(int(ss0)) + ss1
                         ])
    return newvalue
