import numpy as np
import pathlib

__all__ = ["load_txt"]


def parse_metadata(file_metadata):
    """Parse the raw text file metadata information."""
    file_metadata = [m for m in file_metadata if m != '\n']
    file_metadata = [_d.strip('\n').split('\t') for _d in file_metadata]

    # handle each weirdly written piece of metadata
    notes = {}
    for sublist in file_metadata:
        if len(sublist) % 2 == 0:
            even, odd = sublist[::2], sublist[1::2]
            notes.update(dict(zip(even, odd)))
        elif len(sublist) == 1:

            if sublist[0].count(":") == 1:
                notes[sublist[0].split(":")[0]] = sublist[0].split(":")[1]
                continue

            # try to split by whitespace and units within parentheses
            split_sublist = sublist[0].split(' ')
            if len(split_sublist) % 2 == 0:
                notes[split_sublist[0]] = split_sublist[1]
            elif len(split_sublist) == 1:
                # no value
                notes[sublist[0]] = sublist[0]
            else:
                if "(" in sublist[0] and ")" in sublist[0]:
                    assert "(" in split_sublist[1]  # should be the second part
                    notes[split_sublist[0] + " " + split_sublist[1]] = \
                        split_sublist[2]

    # cleanup trailing whitespaces
    for key, val in notes.items():
        notes[key] = val.strip()
    return notes


def open_check_content(path):
    with path.open() as fd:
        txtdata = fd.readlines()

    valid = False
    ind = None
    for line in txtdata:
        if "Device:	Chiaro" in line:
            valid = True
        elif "Time (s)\tLoad" in line:
            ind = txtdata.index(line)
    if not valid:
        raise ValueError

    _metadata = txtdata[:ind]
    _columns = txtdata[ind].strip('\n').split('\t')
    _data = txtdata[ind + 1:]
    _data_split = [_d.strip('\n').split('\t') for _d in _data]
    _data = np.asarray(_data_split).astype(float)
    assert len(_columns) == _data.shape[1]

    return _metadata, _columns, _data


def detect_txt(path):
    """File should be plain text"""
    valid = False
    try:
        _metadata, _columns, _data = open_check_content(path)
    except (ValueError, IndexError):
        pass
    else:
        if np.issubdtype(_data.dtype, np.floating):
            valid = True
    return valid


def load_txt(path, callback=None, meta_override=None):
    """Load text files exported by the Optics11 Chiaro Indenter.

    The columns are assumed to be: todo

    This loader does todo

    Test data were provided by todo

    Parameters
    ----------
    path: str or pathlib.Path or io.TextIOBase
        path to an chiaro-exported .txt file
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

    _metadata, _columns, _data = open_check_content(path)

    data = {"time": _data[:, 0]}
    data["force"] = _data[:, 1] * 1e-6  # load (uN)
    data["height (measured)"] = _data[:, 2] * 1e-9  # indentation (nm)
    data["height (piezo)"] = _data[:, 4] * 1e-9  # piezo (nm)

    max_force_ind = np.argmax(data["force"])

    data["segment"] = np.zeros(_data.shape[0], dtype=np.uint8)
    data["segment"][:max_force_ind + 1] = 0
    data["segment"][max_force_ind + 1:] = 1

    notes = parse_metadata(_metadata)

    # Metadata
    metadata = {}
    metadata["duration"] = float(np.max(data["time"]))
    # acquisition
    metadata["imaging mode"] = "force-distance"
    metadata["feedback mode"] = "contact"
    # metadata["rate approach"] = float(notes["NumPtsPerSec"])
    # metadata["rate retract"] = float(notes["NumPtsPerSec"])
    # metadata["sensitivity"] = float(notes["InvOLS"])
    # if notes["TriggerChannel"] == "Force":
    #     metadata["setpoint"] = float(notes["TriggerPoint"])
    metadata["spring constant"] = float(notes["k (N/m)"])

    # dataset
    metadata["enum"] = 0
    # metadata["speed approach"] = float(notes["ApproachVelocity"])
    # metadata["speed retract"] = float(notes["RetractVelocity"])

    # setup
    metadata["instrument"] = notes["Device:"]
    metadata["software"] = notes["Device:"]
    metadata["software version"] = notes["Software version"]

    # storage
    metadata["path"] = pathlib.Path(path)
    metadata["date"] = notes["Date"]
    metadata["point count"] = data["time"].shape[0]
    metadata["time"] = notes["Time"]

    metadata.update(meta_override)

    dd = {"data": data,
          "metadata": metadata}

    if callback is not None:
        callback(1)

    return [dd]


recipe_chiaro_txt = {
    "descr": "exported by Optics11 Chiaro Indenter",
    "detect": detect_txt,
    "loader": load_txt,
    "suffix": ".txt",
    "modalities": ["force-distance"],
    "maker": "Optics11 Life",
}
