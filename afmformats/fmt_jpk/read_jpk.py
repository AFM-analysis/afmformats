"""Methods to open JPK data files and to obtain meta data"""
from .jpk_reader import JPKReader


def load_jpk(path, callback=None):
    """Extracts force, measured height, and time from JPK files

    All columns are returned in SI units.

    Parameters
    ----------
    path: str
        Path to a JPK force file
    callback: callable or None
        A method that accepts a float between 0 and 1
        to externally track the process of loading the data.
    """
    if callback:
        callback(0)
    # Instantiate JPKReader
    jpkr = JPKReader(path)

    measurements = []
    for index in range(len(jpkr)):
        segments = jpkr.get_index_segment_numbers(index)
        mm = []
        for seg in segments:
            mdi = jpkr.get_metadata(index, seg)
            data = dict()
            data["time"] = jpkr.get_data("time", index, seg)
            data["force"] = jpkr.get_data("force", index, seg)
            data["height (measured)"] = jpkr.get_data("height (measured)",
                                                      index, seg)
            data["height (piezo)"] = jpkr.get_data("height (piezo)",
                                                   index, seg)
            mm.append([data, mdi, path])
        measurements.append(mm)

        if callback:
            # Callback with a float between 0 and 1 to update
            # a progress dialog or somesuch.
            callback(index / len(jpkr))

    return measurements
