import json
import pathlib

import numpy as np

from .afm_data import column_dtypes, known_columns


__all__ = ["load_tab"]


def detect_tab(path, max_header=1000):
    """Test whether `path` is in the tab format"""
    has_begin = False
    has_data = False
    has_end = False
    with path.open() as fd:
        for _ in range(max_header):
            line = fd.readline().strip()
            if line.startswith("# BEGIN METADATA"):
                has_begin = True
            elif line.startswith("# END METADATA") and has_begin:
                has_end = True
            elif len(line) == 0 or line.startswith("#"):
                continue
            else:
                # make sure the first line contains actual floats
                if line.count("\t"):
                    has_data = True
                break
    return has_begin and has_data and has_end


def load_tab(path, callback=None, meta_override=None):
    """Loads tab-separated-value files as exported by afmformats

    This is a simple tab-separated values files. The metadata
    may be present at the beginning of the file, commented out,
    as a json dump in a "BEGIN METADATA" - "END METADATA" block.
    The column data is listed below as a simple table.

    Parameters
    ----------
    path: str or pathlib.Path or io.TextIOBase
        path to a .tab file
    callback: callable
        function for progress tracking; must accept a float in
        [0, 1] as an argument.
    meta_override: dict
        if specified, contains key-value pairs of metadata that
        are used when loading the files
        (see :data:`afmformats.meta.META_FIELDS`)
    """
    if meta_override is None:
        meta_override = {}
    path = pathlib.Path(path)
    with path.open() as fd:
        tsvdata = fd.readlines()

    # get the metadata
    dump = []
    injson = False
    for ii, line in enumerate(tsvdata):
        if line.startswith("# BEGIN METADATA"):
            injson = True
            continue
        elif line.startswith("# END METADATA"):
            break
        elif injson:
            dump.append(line.strip("#").strip())
    if dump:
        metadata = json.loads("\n".join(dump))
    else:
        metadata = {}
    metadata["path"] = path
    metadata["enum"] = 0

    # last line with a hash is the header
    for ii, line in enumerate(tsvdata):
        if not line.strip():
            # empty line
            pass
        elif line.startswith("#"):
            # header candidate
            header_line = line
        else:
            if ii == 0:
                raise ValueError("No header found in '{}'!".format(path))
            break
    else:
        raise ValueError("No data found in '{}'!".format(path))
    columns = header_line.strip("#").strip().split("\t")

    # load the data
    da = [f.strip() for f in tsvdata if f.strip() and not f.startswith("#")]
    # generate arrays
    data = {}
    for cc in columns:
        if cc in known_columns:
            data[cc] = np.zeros(len(da), dtype=column_dtypes[cc])
    for ii, line in enumerate(da):
        for jj, item in enumerate(line.strip().split("\t")):
            assert jj < len(columns)
            cc = columns[jj]
            if cc in known_columns:
                data[cc][ii] = string_to_dtype(item, column_dtypes[cc])

    metadata.update(meta_override)
    dd = {"data": data,
          "metadata": metadata}

    if callback is not None:
        callback(1)

    return [dd]


def string_to_dtype(astring, dtype):
    astring = astring.strip()
    if dtype == bool:
        return astring.lower() == "true"
    elif dtype in [float, int]:
        return dtype(astring)
    else:
        raise ValueError("No conversion rule for dtype '{}'!".format(dtype))


recipe_tab = {
    "descr": "tab-separated values",
    "detect": detect_tab,
    "loader": load_tab,
    "suffix": ".tab",
    "mode": "force-distance",
    "maker": "afmformats",
}
