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


def detect_txt(path):
    """File should be plain text"""
    valid = False
    try:
        rawdata = np.loadtxt(path, converters=converters, max_rows=10)
    except ValueError:
        pass
    else:
        if np.issubdtype(rawdata.dtype, np.floating):
            valid = True
    return valid


def load_txt(path, callback=None, meta_override=None):
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

    Note that support for the original .mdt files is currently (2020)
    not possible. There exist binary readers for nt-mdt files
    (https://github.com/kaitai-io/kaitai_struct/), but this does
    not work for `exemplary data
    <https://doi.org/10.6084/m9.figshare.11862327.v1>`_. If the
    NT-MDT Nova software is not available, it should still be
    possible to load the data with `Ggyddion <http://gwyddion.net>`_
    and export it to something afmformats understands.
    """
    if meta_override is None:
        meta_override = {}
    req_metadata = ["sensitivity", "spring constant"]
    mis_metadata = [key for key in req_metadata if key not in meta_override]
    if mis_metadata:
        raise errors.MissingMetaDataError(
            mis_metadata,
            f"Please specify {' and '.join(mis_metadata)}!")

    rawdata = np.loadtxt(path, converters=converters)

    if rawdata.shape[1] != 3:
        raise errors.InvalidFileFormatError(
            "Expected 3 columns, got {}: {}".format(rawdata.shape[1], path))

    raw_apr = crop_beginning(rawdata[:, :2])
    raw_ret = crop_beginning(rawdata[:, ::2])

    data = {"height (measured)": np.concatenate((raw_apr[::-1, 0],
                                                 raw_ret[:, 0])) * 1e-9}
    fmult = meta_override["sensitivity"] * meta_override["spring constant"]
    data["force"] = np.concatenate((raw_apr[::-1, 1],
                                    raw_ret[:, 1])) * fmult * 1e-9
    data["segment"] = np.concatenate((np.zeros(raw_apr.shape[0], dtype=bool),
                                      np.ones(raw_ret.shape[0], dtype=bool)))

    metadata = {"path": path,
                "enum": 0}
    metadata.update(meta_override)

    dd = {"data": data,
          "metadata": metadata}
    return [dd]


recipe_ntmdt_txt = {
    "descr": "exported by NT-MDT Nova",
    "detect": detect_txt,
    "loader": load_txt,
    "suffix": ".txt",
    "mode": "force-distance",
    "maker": "NT-MDT Spectrum Instruments",
}
