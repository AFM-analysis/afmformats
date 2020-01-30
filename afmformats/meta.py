import pathlib

import numpy as np

from .parse_funcs import fint, vd_str_in


#: Definition of metadata related to the data generated
#: (dictionary with metadata keys, descriptions, units, and validators)
DEF_DATASET = {
    "identifier": ["Measurement identifier", "", str],
    "path": ["Measurement path", "", pathlib.Path],
    "session": ["Recording session identifier", "", str],
}

#: Definition of metadata related to the AFM experiment
#: (dictionary with metadata keys, descriptions, units, and validators)
DEF_EXPERIMENT = {
    "duration": ["Data acquisition time", "s", float],
    "enum": ["Dataset index in the experiment", "", fint],
    "feedback mode": ["Feedback mode", "", vd_str_in([
        # JPK contact mode
        "contact",
        # From the NanoWizard User Manual (v. 4.2) sec. 5.7:
        # Force modulation mode is a mixture between contact mode and
        # intermittend mode and "can be thought of as a kind of contact
        # mode with an added vibration on the cantilever".
        "force-modulation",
    ])],
    "imaging mode": ["Imaging modality", "", vd_str_in(["force-distance"])],
    "point count": ["Size of the dataset in points", "", fint],
    "rate": ["Data recording rate", "Hz", float],
    "sensitivity": ["Sensitivity", "m/V", float],
    "setpoint": ["Active feedback loop setpoint", "N", float],
    "speed": ["Piezo speed", "m/s", float],
    "spring constant": ["Cantilever spring constant", "N/m", float],
    "z range": ["Axial piezo range covered", "m", float],
}

#: Definition of metadata related to quantitative maps
#: (dictionary with metadata keys, descriptions, units, and validators)
DEF_QMAP = {
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
}


#: Definition of metadata related to data analysis
#: (dictionary with metadata keys, descriptions, units, and validators)
DEF_ANALYSIS = {
}

#: A dictionary for all metadata definitions
DEF_ALL = {}
DEF_ALL.update(DEF_DATASET)
DEF_ALL.update(DEF_EXPERIMENT)
DEF_ALL.update(DEF_QMAP)
DEF_ALL.update(DEF_ANALYSIS)

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

    def get_summary(self):
        """Convenience function returning the meta data summary

        Returns a dict of dicts with keys matching the DEF_* dicts.
        Unset values are returned as `np.nan`.
        """
        dataset = {}
        for key in DEF_DATASET:
            dataset[key] = self.get(key, np.nan)
        experiment = {}
        for key in DEF_EXPERIMENT:
            experiment[key] = self.get(key, np.nan)
        qmap = {}
        for key in DEF_QMAP:
            qmap[key] = self.get(key, np.nan)
        analysis = {}
        for key in DEF_ANALYSIS:
            analysis[key] = self.get(key, np.nan)

        summary = {"dataset": dataset,
                   "experiment": experiment,
                   "qmap": qmap,
                   "analysis": analysis,
                   }
        return summary
