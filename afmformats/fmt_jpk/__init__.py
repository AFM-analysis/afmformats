import pathlib

import numpy as np
from . import read_jpk


__all__ = ["load_jpk"]


def load_jpk(path, callback=None):
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
        data["segment"] = np.concatenate((np.zeros(lenapp, dtype=bool),
                                          np.ones(lenret, dtype=bool)))
        dataset.append({"data": data,
                        "metadata": metadata,
                        })
    return dataset


recipe_jpk_force = {
    "loader": load_jpk,
    "suffix": ".jpk-force",
    "mode": "force-distance",
    "maker": "JPK Instruments",
}

recipe_jpk_force_map = {
    "loader": load_jpk,
    "suffix": ".jpk-force-map",
    "mode": "force-distance",
    "maker": "JPK Instruments",
}
