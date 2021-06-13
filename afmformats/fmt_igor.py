import pathlib

from igor import binarywave
import numpy as np

__all__ = ["load_igor"]


def load_igor(path, callback=None, meta_override=None):
    """Load Asylum Research (Igor) binarywave .ibw files

    The raw data are loaded with the Python module "igor"
    (http://blog.tremily.us/posts/igor/).
    The way column labels are assigend to the data is kind of hacky.
    The metadata assignment is largely guessed.

    Test data were provided by Nicolas Hauck :cite:`Hauck2018`.

    Parameters
    ----------
    path: str or pathlib.Path
        path to in .ibw data file
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

    ibw = binarywave.load(path)
    wdata = ibw["wave"]["wData"]
    notes = {}
    for line in str(ibw["wave"]["note"]).split("\\r"):
        if line.count(":"):
            key, val = line.split(":", 1)
            notes[key] = val.strip()

    # Metadata
    metadata = {}
    # acquisition
    metadata["imaging mode"] = "force-distance"
    metadata["feedback mode"] = notes["ImagingMode"].lower()
    metadata["rate approach"] = float(notes["NumPtsPerSec"])
    metadata["rate retract"] = float(notes["NumPtsPerSec"])
    metadata["sensitivity"] = float(notes["InvOLS"])
    if notes["TriggerChannel"] == "Force":
        metadata["setpoint"] = float(notes["TriggerPoint"])
    metadata["spring constant"] = float(notes["SpringConstant"])

    # dataset
    metadata["duration"] = float(notes["InputTime"])
    metadata["enum"] = 1
    metadata["speed approach"] = float(notes["ApproachVelocity"])
    metadata["speed retract"] = float(notes["RetractVelocity"])

    # setup
    metadata["instrument"] = notes["MicroscopeModel"]
    metadata["software"] = "Asylum Research"
    metadata["software version"] = notes["Version"]

    # storage
    metadata["date"] = notes["Date"]
    metadata["path"] = pathlib.Path(path)
    metadata["point count"] = wdata.shape[0]
    metadata["time"] = notes["Time"]

    # Data
    labels = []
    # deal with something like this:
    # 'labels': [[], [b'', b'Raw', b'Defl', b'ZSnsr'], [], []],
    for ll in ibw["wave"]["labels"]:
        for li in ll:
            if li:
                labels.append(li.decode())
    assert len(labels) == wdata.shape[1]

    data = {}
    for pkey in ["Raw", "Height"]:
        if pkey in labels:
            # height is in [m]
            data["height (piezo)"] = -wdata[:, labels.index(pkey)]
            break

    for mkey in ["ZSnsr", "ZSensor"]:
        if mkey in labels:
            # height is in [m]
            data["height (measured)"] = -wdata[:, labels.index(mkey)]
            break

    for fkey in ["Defl", "Deflection"]:
        if fkey in labels:
            # force is in [m] (convert to [N])
            data["force"] = wdata[:, labels.index(fkey)] \
                * metadata["spring constant"]
            break

    data["segment"] = np.zeros(wdata.shape[0], dtype=bool)

    # missing metadata
    metadata["z range"] = np.ptp(data["height (piezo)"])
    metadata.update(meta_override)

    dataset = [{"data": data,
                "metadata": metadata,
                }]

    if callback is not None:
        callback(1)

    return dataset


recipe_ibw = {
    "descr": "binarywave",
    "loader": load_igor,
    "suffix": ".ibw",
    "mode": "force-distance",
    "maker": "Asylum Research",
}
