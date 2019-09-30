import pathlib

import numpy as np

from .afm_fdist import column_dtypes, known_columns


def load_tab(path, callback=None):
    """Loads tab-separated-value files as exported by afmformats"""
    path = pathlib.Path(path)
    with path.open() as fd:
        # first line is the header
        columns = fd.readline().strip("#").strip().split("\t")
        da = [f for f in fd.readlines() if f.strip() and not f.startswith("#")]
        # generate arrays
        data = {}
        for cc in columns:
            if cc in known_columns:
                data[cc] = np.zeros(len(da), dtype=column_dtypes[cc])
        for ii, line in enumerate(da):
            for jj, item in enumerate(line.split("\t")):
                cc = columns[jj]
                if cc in known_columns:
                    data[cc][ii] = string_to_dtype(item, column_dtypes[cc])

    dd = {"data": data,
          "metadata": {"enum": 0,
                       "path": path}}
    return [dd]


def string_to_dtype(astring, dtype):
    astring = astring.strip()
    if dtype == bool:
        return astring.lower() == "true"
    elif dtype == float:
        return float(astring)
    else:
        raise ValueError("No conversion rule for dtype '{}'!".format(dtype))


recipe_tab = {
    "loader": load_tab,
    "suffix": ".tab",
    "mode": "force-distance",
}
