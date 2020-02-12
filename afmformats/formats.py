import pathlib

from .fmt_hdf5 import recipe_hdf5
from .fmt_igor import recipe_ibw
from .fmt_jpk import recipe_jpk_force, recipe_jpk_force_map
from .fmt_tab import recipe_tab
from .afm_fdist import AFMForceDistance


__all__ = ["load_data", "formats_available", "formats_by_suffix",
           "formats_by_mode", "supported_extensions"]


def load_data(path, mode=None, diskcache=False, callback=None):
    path = pathlib.Path(path)
    if path.suffix in formats_by_suffix:
        if mode is None:
            # TODO:
            # - Try to figure out the mode somehow
            mode = "force-distance"
        # TODO:
        # - if multiple file types exist, get the right one (not the 1st)
        loader = formats_by_suffix[path.suffix][0]["loader"]
        afmdata = []
        if mode == "force-distance":
            for dd in loader(path, callback=callback):
                ddi = AFMForceDistance(data=dd["data"],
                                       metadata=dd["metadata"],
                                       diskcache=diskcache)
                afmdata.append(ddi)
    else:
        raise ValueError("Unsupported file extension: '{}'!".format(path))
    return afmdata


#: available/supported file formats
formats_available = [
    recipe_hdf5,
    recipe_ibw,
    recipe_jpk_force,
    recipe_jpk_force_map,
    recipe_tab,
]
#: available file formats in a dictionary with suffix keys
formats_by_suffix = {}
# Populate list of available fit models
for _item in formats_available:
    _suffix = _item["suffix"]
    if _suffix not in formats_by_suffix:
        formats_by_suffix[_suffix] = []
    formats_by_suffix[_suffix].append(_item)
#: available file formats in a dictionary with modality keys
formats_by_mode = {}
for _item in formats_available:
    _mode = _item["mode"]
    if _mode not in formats_by_mode:
        formats_by_mode[_mode] = []
    formats_by_mode[_mode].append(_item)
#: list of supported extensions
supported_extensions = sorted(formats_by_suffix.keys())
