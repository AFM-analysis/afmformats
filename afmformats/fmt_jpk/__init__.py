import numpy as np

from ..lazy_loader import LazyData

from .jpk_reader import JPKReader


__all__ = ["JPKReader", "load_jpk"]


def load_jpk(path, callback=None, meta_override=None):
    """Loads JPK Instruments data files

    These files are zip files containing java property files and
    integer-encoded binary data. The property files include recipes
    on how to convert the raw integer data to SI units.
    """
    if meta_override is None:
        meta_override = {}
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
        # TODO: the following line slows things down, refactor?
        metadata["z range"] = np.ptp(lazy_data["height (piezo)"])
        metadata.update(meta_override)
        dataset.append({"data": lazy_data,
                        "metadata": metadata,
                        })
        if callback:
            callback(index / len(jpkr))
    return dataset


recipe_jpk_force = {
    "descr": "binary FD data",
    "loader": load_jpk,
    "maker": "JPK Instruments",
    "mode": "force-distance",
    "suffix": ".jpk-force",
}

recipe_jpk_force_map = {
    "descr": "binary QMap data",
    "loader": load_jpk,
    "maker": "JPK Instruments",
    "mode": "force-distance",
    "suffix": ".jpk-force-map",
}

recipe_jpk_force_qi = {
    "descr": "binary QMap data",
    "loader": load_jpk,
    "maker": "JPK Instruments",
    "mode": "force-distance",
    "suffix": ".jpk-qi-data",
}
