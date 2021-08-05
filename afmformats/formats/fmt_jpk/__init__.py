import numpy as np

from ...lazy_loader import LazyData
from ...meta import LazyMetaValue

from .jpk_reader import JPKReader
from .jpk_meta import ReadJPKMetaKeyError


__all__ = ["load_jpk"]


def detect(path):
    """Check whether a file is a valid JPK data file

    """
    # The suffix is not checked, because that is done in
    # the wrapper class formats.AFMFormatRecipe.
    jpkr = JPKReader(path)
    try:
        jpkr.get_metadata(index=0)
    except ReadJPKMetaKeyError:
        valid = False
    else:
        valid = True
    return valid


def load_jpk(path, callback=None, meta_override=None):
    """Loads JPK Instruments data files

    These files are zip files containing java property files and
    integer-encoded binary data. The property files include recipes
    on how to convert the raw integer data to SI units.

    Parameters
    ----------
    path: str or pathlib.Path
        path to JPK data file
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
    else:
        # just make sure nobody expects a different result for the forces
        for key in ["sensitivity", "spring constant"]:
            if key in meta_override:
                raise NotImplementedError(
                    f"Setting metadata such as '{key}' is not implemented!")

    jpkr = JPKReader(path)
    dataset = []
    # iterate over all datasets and add them
    for index in range(len(jpkr)):
        lazy_data = LazyData()
        for column in ["force", "height (measured)", "height (piezo)",
                       "segment", "time"]:
            lazy_data.set_lazy_loader(column=column,
                                      func=jpkr.get_data,
                                      kwargs={"column": column,
                                              "index": index})
        metadata = jpkr.get_metadata(index=index)
        metadata["z range"] = LazyMetaValue(
            lambda data: np.ptp(data["height (piezo)"]),
            lazy_data)
        metadata.update(meta_override)
        dataset.append({"data": lazy_data,
                        "metadata": metadata,
                        })
        if callback:
            callback((1+index) / len(jpkr))
    return dataset


recipe_jpk_force = {
    "descr": "binary FD data",
    "detect": detect,
    "loader": load_jpk,
    "maker": "JPK Instruments",
    "modalities": ["creep-compliance", "force-distance", "stress-relaxation"],
    "suffix": ".jpk-force",
}

recipe_jpk_force_map = {
    "descr": "binary QMap data",
    "detect": detect,
    "loader": load_jpk,
    "maker": "JPK Instruments",
    "modalities": ["creep-compliance", "force-distance", "stress-relaxation"],
    "suffix": ".jpk-force-map",
}

recipe_jpk_force_qi_data = {
    "descr": "binary QMap data",
    "detect": detect,
    "loader": load_jpk,
    "maker": "JPK Instruments",
    "modalities": ["creep-compliance", "force-distance", "stress-relaxation"],
    "suffix": ".jpk-qi-data",
}

recipe_jpk_force_qi_series = {
    "descr": "binary QMap data",
    "detect": detect,
    "loader": load_jpk,
    "maker": "JPK Instruments",
    "modalities": ["creep-compliance", "force-distance", "stress-relaxation"],
    "suffix": ".jpk-qi-series",
}
