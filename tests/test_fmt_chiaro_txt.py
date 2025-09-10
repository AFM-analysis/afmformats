"""Test NT-MDT text export format"""
import pathlib
import numpy as np

import afmformats

data_path = pathlib.Path(__file__).resolve().parent / "data"


def test_open_simple_txt():
    path = pathlib.Path((r"C:\Users\eoconne\Documents"
                         r"\Students_Colleagues\Alice\afm"
                         r"\Pyjibe_implementation\Data_from_Chiaro"
                         r"\AEBP1_01 Indentation_002.txt"))

    data = afmformats.load_data(path=path)[0]
    assert data["force"].size == 13827
    # maximum force is at end of 1st segment
    assert np.sum(data["segment"] == 0) == np.argmax(data["force"]) + 1


if __name__ == "__main__":
    # Run all tests
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
