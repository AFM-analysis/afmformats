import io
import pathlib
import warnings

import numpy as np

from ... import errors


class AFMWorkshopFormatWarning(UserWarning):
    pass


__all__ = ["load_csv"]


months = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12
}


def load_csv(path, callback=None, meta_override=None, mode="single"):
    """Load csv data from AFM workshop

    The files are structured like this::

        Force-Distance Curve
        File Format:    3

        Date:    Wednesday, August 1, 2018
        Time:    1:07:47 PM
        Mode:    Single
        Point:    1
        X, um:    27.250000
        Y, um:    27.250000

        Extend Z-Sense(nm),Extend T-B(V),Retract Z-Sense(nm),Retract T-B(V)
        13777.9288,0.6875,14167.9288,1.0917
        13778.9288,0.6874,14166.9288,1.0722
        13779.9288,0.6876,14165.9288,1.0693
        13780.9288,0.6877,14164.9288,1.0824
        13781.9288,0.6875,14163.9288,1.0989
        ...

    The data for testing was kindly provided by Peter Eaton
    (afmhelp.com).


    Parameters
    ----------
    path: str or pathlib.Path or io.TextIOBase
        data file or an open file in text (not bytes) mode
    callback: callable
        function for progress tracking; must accept a float in
        [0, 1] as an argument.
    meta_override: dict
        if specified, contains key-value pairs of metadata that
        are used when loading the files
        (see :data:`afmformats.meta.META_FIELDS`)
    mode: str
        curve mode to expect (either "single" or "mapping"); if an
        unexpected mode is found, AFMWorkshopFormatWarning is issued
    """
    if meta_override is None:
        meta_override = {}
    metadata = {}
    # TODO:
    # - only read really the header instead of the entire file to save time
    if isinstance(path, io.IOBase):
        csvdata = path.readlines()
        path.seek(0)  # required for np.loadtxt below
    else:
        path = pathlib.Path(path)
        csvdata = path.read_text(encoding="utf-8").split("\n")
        metadata["path"] = path

    # get the metadata
    for ii, line in enumerate(csvdata):
        if line.count("Force-Distance Curve"):
            metadata["imaging mode"] = "force-distance"
        elif line.startswith("Software Version"):
            metadata["software version"] = line.split(":")[1].strip()
        elif line.startswith("Date:"):
            cdate = parse_date(line.split(":")[1])
            metadata["date"] = cdate
        elif line.startswith("Time:"):
            metadata["time"] = line.split(":", 1)[1]
        elif line.startswith("Mode:"):
            cur_mode = line.split(":")[1].strip().lower()
            if cur_mode != mode:
                warnings.warn(f"Expected '{mode}' curve; got '{cur_mode}'!",
                              AFMWorkshopFormatWarning)
        elif line.startswith("Point:"):
            metadata["enum"] = int(line.split(":")[1])
        elif line.startswith("X, um:"):
            metadata["position x"] = float(line.split(":")[1]) * 1e-6
        elif line.startswith("Y, um:"):
            metadata["position y"] = float(line.split(":")[1]) * 1e-6
        elif line.startswith("Light Lever Gain, mV/nm:"):
            value = float(line.split(":")[1])
            if value != 1:  # ignore default values
                metadata["sensitivity"] = 1 / (value * 1e-3 / 1e-9)
        elif line.startswith("Force Constant, nN/nm:"):
            value = float(line.split(":")[1])
            if value != 1:  # ignore default values
                metadata["spring constant"] = value
        elif line.count(",") >= 3:
            header_index = ii
            header_line = line
            break
    else:
        raise errors.FileFormatNotSupportedError(
            "Could not parse metadata correctly: {}".format(path))

    metadata.update(meta_override)
    req_metadata = ["sensitivity", "spring constant"]
    mis_metadata = [key for key in req_metadata if key not in metadata]
    if mis_metadata:
        fmult = None
    else:
        fmult = metadata["sensitivity"] * metadata["spring constant"]

    if "imaging mode" not in metadata:
        raise errors.FileFormatNotSupportedError(
            "Unknown file format: {}".format(path))

    # load data
    rawdata = np.loadtxt(path, skiprows=header_index+1, delimiter=",")
    segsize = rawdata.shape[0]
    data = {"height (measured)": np.zeros(2*segsize, dtype=float)*np.nan,
            "force": np.zeros(2*segsize, dtype=float)*np.nan,
            "segment": np.concatenate((np.zeros(segsize, dtype=np.uint8),
                                       np.ones(segsize, dtype=np.uint8)))
            }
    columns = header_line.strip().split(",")
    for jj, cc in enumerate(columns):
        if cc == "Extend Z-Sense(nm)":
            data["height (measured)"][:segsize] = -rawdata[:, jj] * 1e-9
        elif cc == "Retract Z-Sense(nm)":
            data["height (measured)"][segsize:] = -rawdata[:, jj] * 1e-9
        elif cc == "Extend T-B(V)":
            if mis_metadata:
                raise errors.MissingMetaDataError(
                    mis_metadata,
                    f"Please specify {' and '.join(mis_metadata)}!")
            else:
                data["force"][:segsize] = rawdata[:, jj] * fmult
        elif cc == "Extend Force(nN)":
            data["force"][:segsize] = rawdata[:, jj] * 1e-9
        elif cc == "Retract T-B(V)":
            if mis_metadata:
                raise errors.MissingMetaDataError(
                    mis_metadata,
                    f"Please specify {' and '.join(mis_metadata)}!")
            else:
                data["force"][segsize:] = rawdata[:, jj] * fmult
        elif cc == "Retract Force(nN)":
            data["force"][segsize:] = rawdata[:, jj] * 1e-9
        else:
            warnings.warn(f"Unknown column encountered: {cc}",
                          AFMWorkshopFormatWarning)

    # remove non-existent or bad data
    for key in list(data.keys()):
        if np.sum(np.isnan(data[key])):
            warnings.warn(f"Removed incomplete column: {key} in {path}!",
                          AFMWorkshopFormatWarning)
            data.pop(key)

    dd = {"data": data,
          "metadata": metadata}

    if callback is not None:
        callback(1)
    return [dd]


def parse_date(datestr):
    """Heuristic function for parsin AFM workshop dates"""
    datestr = datestr.strip()

    if datestr.count(",") == 2:
        # Friday, February 14, 2020
        _, m, d, y = [a.strip(", ") for a in datestr.split()]
    elif datestr.count(",") == 0:
        # 15 January 2021
        d, m, y = [a.strip("") for a in datestr.split()]
    else:
        raise errors.FileFormatMetaDataError(f"Cannot parse date '{datestr}'!")

    return f"{int(y):04d}-{months[m]:02d}-{int(d):02d}"
