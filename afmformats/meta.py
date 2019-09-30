import pathlib

from .parse_funcs import fint, vd_str_in

#: Metadata related to the basic AFM experiment
DEF_BASE = {
    "duration": ["Duration of experiment", "s", float],
    "feedback mode": ["Feedback mode", "", vd_str_in(["contact"])],
    "identifier": ["Unique data identifier", "", str],
    "imaging mode": ["Imaging modality", "", vd_str_in(["force-distance"])],
    "path": ["Path to the measurement file", "", pathlib.Path],
    "point count": ["Size of the dataset in points", "", fint],
    "rate": ["Data recording rate", "Hz", float],
    "sensitivity": ["Sensitivity", "m/V", float],
    "setpoint": ["Active feedback loop setpoint", "N", float],
    "speed": ["Piezo speed", "m/s", float],
    "spring constant": ["Cantilever spring constant", "N/m", float],
    "z range": ["Axial piezo range covered", "m", float],
    }

#: Metadata related to quantitative maps
DEF_QMAP = {
    "enum": ["Datapoint index within the dataset", "", fint],
    "grid center x": ["Horizontal center of grid", "m", float],
    "grid center y": ["Vertical center of grid", "m", float],
    "grid index x": ["Horizontal grid position index", fint],
    "grid index y": ["Vertical grid position index", fint],
    "grid shape x": ["Horizontal grid shape", "px", fint],
    "grid shape y": ["Vertical grid shape", "px", fint],
    "grid size x": ["Horizontal grid size", "m", float],
    "grid size y": ["Vertical grid size", "m", float],
    "position x": ["Horizontal position", "m", float],
    "position y": ["Vertical position", "m", float],
    }

#: Metadata related to data analysis
DEF_ANALYSIS = {
    }

KEYS_VALID = sorted(list(DEF_BASE.keys())
                    + list(DEF_QMAP.keys())
                    + list(DEF_ANALYSIS.keys()))


class MetaDataMissingError(BaseException):
    """Raised when meta data is missing"""
    pass


class MetaData(dict):
    """Management of meta data variables

    Valid key names are defined in :const:`afmformats.meta.KEYS_VALID`.
    """
    valid_keys = KEYS_VALID

    def __init__(self, *args, **kwargs):
        super(MetaData, self).__init__(*args, **kwargs)
        # check for invalid keys
        for key in self:
            if key not in self.valid_keys:
                raise KeyError("Unknown metadata key: '{}'".format(key))

    def __setitem__(self, key, value):
        """Set a metadata key

        The key must be a valid key defined in `self.valid_keys`
        (defaults to :const:`afmformats.meta.KEYS_VALID`).
        """
        if key not in self.valid_keys:
            raise KeyError("Unknown metdataa key: '{}'".format(key))
        super(MetaData, self).__setitem__(key, value)

    def __getitem__(self, *args, **kwargs):
        if args[0] not in self and args[0] in self.valid_keys:
            msg = "No meta data was defined for '{}'!".format(args[0]) \
                  + "Please make sure you passed the dictionary `metadata` " \
                  + "when you loaded your data."
            raise MetaDataMissingError(msg)
        elif args[0] not in self:
            msg = "Unknown meta key: '{}'!".format(args[0])
            raise KeyError(msg)
        return super(MetaData, self).__getitem__(*args, **kwargs)


