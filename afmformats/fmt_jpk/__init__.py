import pathlib

import numpy as np
from .read_jpk import load_jpk


def prepare_jpk_data(path, callback=None):
    """Convert the data from `load_jpk` to something afmformats understands"""
    # load the data
    measurements = load_jpk(path=path, callback=callback)
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
    "loader": prepare_jpk_data,
    "suffix": ".jpk-force",
    "mode": "force-distance",
}

recipe_jpk_force_map = {
    "loader": prepare_jpk_data,
    "suffix": ".jpk-force-map",
    "mode": "force-distance",
}
