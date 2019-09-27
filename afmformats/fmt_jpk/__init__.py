import pathlib

from pandas import DataFrame
from .read_jpk import load_jpk


def prepare_jpk_data(path, callback=None):
    """Convert the data from `load_jpk` to something afmformats understands"""
    # load the data
    measurements = load_jpk(path=path, callback=callback)
    # convert join the segment data
    dataset = []
    for enum, mm in enumerate(measurements):
        app, ret = mm
        metadata = app[1]
        metadata["enum"] = enum
        metadata["path"] = pathlib.Path(path)

        # join segments
        app = DataFrame(app[0])
        app["segment"] = False
        ret = DataFrame(ret[0])
        ret["segment"] = True
        ret["time"] += metadata["duration [s]"]
        ret.index += len(app.index)
        data = app.append(ret)
        dataset.append({"data": data,
                        "metadata": metadata,
                        })

    return dataset


fmt_jpk_force = {
    "loader": prepare_jpk_data,
    "suffix": ".jpk-force",
    "mode": "force-distance",
}

fmt_jpk_force_map = {
    "loader": prepare_jpk_data,
    "suffix": ".jpk-force-map",
    "mode": "force-distance",
}
