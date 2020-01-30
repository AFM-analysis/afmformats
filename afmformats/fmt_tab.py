import json
import pathlib

import numpy as np

from .afm_fdist import column_dtypes, known_columns


def load_tab(path, callback=None):
    """Loads tab-separated-value files as exported by afmformats"""
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

    dd = {"data": data,
          "metadata": metadata}
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
    "loader": load_tab,
    "suffix": ".tab",
    "mode": "force-distance",
}
