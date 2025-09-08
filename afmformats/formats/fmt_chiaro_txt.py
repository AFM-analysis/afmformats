import numpy as np

from .. import errors


__all__ = ["load_txt"]



def format_metadata(_metadata):
    # todo: known_columns

    _metadata = [m for m in _metadata if m != '\n']
    _metadata = [_d.strip('\n').split('\t') for _d in _metadata]

    # handle each weirdly written piece of metadata
    metadata = {}
    for sublist in _metadata:
        if len(sublist) % 2 == 0:
            even, odd = sublist[::2], sublist[1::2]
            metadata.update(dict(zip(even, odd)))
        elif len(sublist) == 1:

            if sublist[0].count(":") == 1:
                metadata[sublist[0].split(":")[0]] = sublist[0].split(":")[1]
                continue

            # try to split by whitespace and units within parentheses
            split_sublist = sublist[0].split(' ')
            if len(split_sublist) % 2 == 0:
                metadata[split_sublist[0]] = split_sublist[1]
            elif len(split_sublist) == 1:
                # no value
                metadata[sublist[0]] = sublist[0]
            else:
                if "(" in sublist[0] and ")" in sublist[0]:
                    assert "(" in split_sublist[1]  # should be the second part
                    metadata[
                        split_sublist[0] + " " + split_sublist[1]] = split_sublist[2]

    # cleanup trailing whitespaces
    for key, val in metadata.items():
        metadata[key] = val.strip()

    return metadata

def crop_beginning(data):
    """Crop constant padding at the start of the data column"""
    assert data.shape[1] == 2

    start = data[0, 1]
    for ii in range(1, data.shape[0]):
        if data[ii, 1] != start:
            break
    else:
        raise ValueError("Encountered all-constant data!")

    return data[ii-1:, :]
def open_check_content(path):
    with path.open() as fd:
        txtdata = fd.readlines()

    for line in txtdata:
        if "Time (s)" in line:
            ind = txtdata.index(line)

    _metadata = txtdata[:ind]
    _columns = txtdata[ind].strip('\n').split('\t')
    _data = txtdata[ind+1:]
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
    _metadata = format_metadata(_metadata)

    # raw_apr = crop_beginning(rawdata[:, :2])
    # raw_ret = crop_beginning(rawdata[:, ::2])

    data = {"height (measured)": np.concatenate((raw_apr[::-1, 0],
                                                 raw_ret[:, 0])) * 1e-9}
    fmult = meta_override["sensitivity"] * meta_override["spring constant"]
    data["force"] = np.concatenate((raw_apr[::-1, 1],
                                    raw_ret[:, 1])) * fmult * 1e-9
    data["segment"] = np.concatenate(
        (np.zeros(raw_apr.shape[0], dtype=np.uint8),
         np.ones(raw_ret.shape[0], dtype=np.uint8)))

    metadata = {"enum": 0,
                "imaging mode": "force-distance",
                "path": path,
                }
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
