import pathlib

import numpy as np

from .jpk_reader import JPKReader  # noqa: F401
from . import read_jpk


__all__ = ["JPKReader", "load_jpk"]


def load_jpk(path, callback=None, meta_override={}):
    """Loads JPK Instruments data files

    These files are zip files containing java property files and
    integer-encoded binary data. The property files include recipes
    on how to convert the raw integer data to SI units.
    """
    # load the data
    measurements = read_jpk.load_jpk(path=path, callback=callback)
    # convert join the segment data
    dataset = []
    for mm in measurements:
        (app, metadata, _), (ret, metadata_ret, _) = mm
        metadata["path"] = pathlib.Path(path)
        metadata["duration"] += metadata_ret["duration"]
        metadata["rate retract"] = metadata_ret["rate retract"]
        metadata["point count"] += metadata_ret["point count"]
        metadata["speed retract"] = metadata_ret["speed retract"]
        # join segments
        lenapp = len(app[list(app.keys())[0]])
        lenret = len(ret[list(ret.keys())[0]])
        ret["time"] += metadata["duration"]
        data = {}
        for key in app.keys():
            data[key] = np.concatenate((app[key], ret[key]))
        metadata["z range"] = np.ptp(data["height (piezo)"])
        data["segment"] = np.concatenate((np.zeros(lenapp, dtype=bool),
                                          np.ones(lenret, dtype=bool)))
        metadata.update(meta_override)
        dataset.append({"data": data,
                        "metadata": metadata,
                        })
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
