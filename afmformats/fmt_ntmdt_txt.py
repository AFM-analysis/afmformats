import numpy as np

from . import errors


__all__ = ["load_txt"]


converters = {
    0: lambda s: float(s.decode().strip().replace(",", ".")),
    1: lambda s: float(s.decode().strip().replace(",", ".")),
    2: lambda s: float(s.decode().strip().replace(",", ".")),
}


def crop_beginning(data):
    """Crop constant padding at the begin of the data column"""
    assert data.shape[1] == 2

    start = data[0, 1]
    for ii in range(1, data.shape[0]):
        if data[ii, 1] != start:
            break
    else:
        raise ValueError("Encountered all-constant data!")

    return data[ii-1:, :]


def load_txt(path, callback=None, meta_override={}):
    """Load text files exported by the NT-MDT Nova software

    The columns are assumed to be: height (piezo) [nm],
    Deflection during approach (nA), Deflection during retraction (nA).
    The sensitivity in meta_override should be given in [m/A]
    (even though it is displayed as [m/V]).

    This loader removes constant-value padding at the beginning of
    the data columns, an artifact that is sometimes introduced during
    data export. There are no metadata in this file format.

    Test data were provided by Yuri Efremov
    :cite:`Efremov_figshare_20` :cite:`Efremov_2015`.
    """
    if ("sensitivity" not in meta_override
            and "spring constant" not in meta_override):
        raise errors.MissingMetaDataError(
            "Please specify 'spring constant' and 'sensitivity'!")

    rawdata = np.loadtxt(path, converters=converters)

    if rawdata.shape[1] != 3:
        raise errors.InvalidFileFormatError(
            "Expected 3 columns, got {}: {}".format(rawdata.shape[1], path))

    raw_apr = crop_beginning(rawdata[:, :2])
    raw_ret = crop_beginning(rawdata[:, ::2])

    data = {}
    data["height (measured)"] = np.concatenate((raw_apr[::-1, 0],
                                                raw_ret[:, 0])) * 1e-9
    fmult = meta_override["sensitivity"] * meta_override["spring constant"]
    data["force"] = np.concatenate((raw_apr[::-1, 1],
                                    raw_ret[:, 1])) * fmult * 1e-9
    data["segment"] = np.concatenate((np.zeros(raw_apr.shape[0], dtype=bool),
                                      np.ones(raw_ret.shape[0], dtype=bool)))

    metadata = {}
    metadata["path"] = path
    metadata["enum"] = 0
    metadata.update(meta_override)

    dd = {"data": data,
          "metadata": metadata}
    return [dd]


recipe_ntmdt_txt = {
    "descr": "exported by NT-MDT Nova",
    "loader": load_txt,
    "suffix": ".txt",
    "mode": "force-distance",
    "maker": "NT-MDT Spectrum Instruments",
}
