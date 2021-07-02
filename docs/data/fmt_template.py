import pathlib

import numpy as np


__all__ = ["load_my_format"]


def load_my_format(path, callback=None, meta_override=None):
    """Loads AFM data from my format

    This is the main function for loading your file format. Please
    add a description here.

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
    # Here you would start parsing your data and metadata from `path`
    # You should specify as many metadata keys as possible. See
    # afmformats.meta.DEF_ALL for a list of valid keys.
    metadata = {"path": path}
    # Valid column names are defined in afmformats.afm_data.known_columns.
    data = {"force": np.linspace(1e-9, 5e-9, 100),
            "height (measured)": np.linspace(2e-6, -1e-6, 100)}

    metadata.update(meta_override)
    dd = {"data": data,
          "metadata": metadata}

    if callback is not None:
        callback(1)

    # You may also return a list with more items in case the file format
    # contains more than one curve.
    return [dd]


recipe_myf = {
    "descr": "A short description",
    "loader": load_my_format,
    "suffix": ".myf",
    "modality": "force-distance",
    "maker": "designer of file format",
}
