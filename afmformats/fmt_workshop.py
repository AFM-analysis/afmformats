import pathlib
import warnings

import numpy as np

from . import errors


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


def load_csv(path, callback=None, meta_override={}):
    """Load csv data from AFM workshop


    The files are structured like this::

        Force-Distance Curve
        File Format:    3

        Date:    Wednesday, August 1, 2018
        Time:    1:07:47 PM
        Mode:    Mapping
        Point:    16
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
    """
    path = pathlib.Path(path)
    with path.open() as fd:
        csvdata = fd.readlines()

    # get the metadata
    metadata = {}
    for ii, line in enumerate(csvdata):
        if line.count("Force-Distance Curve"):
            metadata["imaging mode"] = "force-distance"
        elif line.startswith("Date:"):
            _, m, d, y = [a.strip(", ") for a in line.split(":")[1].split()]
            metadata["date"] = "{:04d}-{:02d}-{:02d}".format(int(y),
                                                             months[m],
                                                             int(d))
        elif line.startswith("Time:"):

            time, ap = line.split(":", 1)[1].split()
            timetup = time.split(":")
            if ap == "PM":  # convert to 24h
                timetup[0] = str(int(timetup[0]) + 12)
            else:  # add leading 0 if necessary
                timetup[0] = "{:02d}".format(int(timetup[0]))
            time = ":".join(timetup)
            metadata["time"] = time
        elif line.startswith("Mode:"):
            # TODO: how should we deal with mapping?
            pass
        elif line.startswith("Point:"):
            metadata["enum"] = int(line.split(":")[1])
        elif line.startswith("X, um:"):
            metadata["position x"] = float(line.split(":")[1]) * 1e-6
        elif line.startswith("Y, um:"):
            metadata["position y"] = float(line.split(":")[1]) * 1e-6
        elif line.count(",") >= 3:
            header_index = ii
            header_line = line
            break
    else:
        raise errors.FileFormatNotSupportedError(
            "Could not parse metadata correctly: {}".format(path))

    metadata["path"] = path

    metadata.update(meta_override)

    if "imaging mode" not in metadata:
        raise errors.FileFormatNotSupportedError(
            "Unknown file format: {}".format(path))

    # load data
    if "sensitivity" in metadata and "spring constant" in metadata:
        fmult = metadata["sensitivity"] * metadata["spring constant"]
    else:
        errmsg = "Cannot load column '{}', because spring constant and " \
                 + "sensitivity were neither found in '{}' ".format(path) \
                 + "nor in the keyword argument `meta_override`!"
        fmult = None
    rawdata = np.loadtxt(path, skiprows=header_index+1, delimiter=",")
    segsize = rawdata.shape[0]
    data = {"height (measured)": np.zeros(2*segsize, dtype=float)*np.nan,
            "force": np.zeros(2*segsize, dtype=float)*np.nan,
            "segment": np.concatenate((np.zeros(segsize, dtype=bool),
                                       np.ones(segsize, dtype=bool)))
            }
    columns = header_line.strip().split(",")
    for jj, cc in enumerate(columns):
        if cc == "Extend Z-Sense(nm)":
            data["height (measured)"][:segsize] = -rawdata[:, jj] * 1e-9
        elif cc == "Retract Z-Sense(nm)":
            data["height (measured)"][segsize:] = -rawdata[:, jj] * 1e-9
        elif cc == "Extend T-B(V)":
            if fmult is None:
                raise errors.MissingMetaDataError(errmsg.format(cc))
            else:
                data["force"][:segsize] = rawdata[:, jj] * fmult
        elif cc == "Extend Force(nN)":
            data["force"][:segsize] = rawdata[:, jj] * 1e-9
        elif cc == "Retract T-B(V)":
            if fmult is None:
                raise errors.MissingMetaDataError(errmsg.format(cc))
            else:
                data["force"][segsize:] = rawdata[:, jj] * fmult
        elif cc == "Retract Force(nN)":
            data["force"][segsize:] = rawdata[:, jj] * 1e-9
        else:
            warnings.warn("Unknown column encountered: {}".format(cc))

    # remove non-existent or bad data
    for key in list(data.keys()):
        if np.sum(np.isnan(data[key])):
            warnings.warn("Removed incomplete column: {} in {}!".format(key,
                                                                        path))
            data.pop(key)

    dd = {"data": data,
          "metadata": metadata}
    return [dd]


recipe_workshop = {
    "descr": "comma-separated values",
    "loader": load_csv,
    "suffix": ".csv",
    "mode": "force-distance",
    "maker": "AFM workshop",
}
