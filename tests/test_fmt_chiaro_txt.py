"""Test NT-MDT text export format"""
import pathlib
import tempfile

import numpy as np
import pytest
from nptdms import TdmsFile

import afmformats


data_path = pathlib.Path(__file__).resolve().parent / "data"


def test_load_tdms():
    path = r"C:\Users\eoconne\Documents\Students_Colleagues\Alice\afm\Pyjibe_implementation\Data_from_Chiaro\AEBP1_01 Indentation_002.tdms"
    file = TdmsFile(path)
    groups = file.groups()
    channels = file.groups()[0].channels()
    print("")


def test_open_simple_txt():
    path =pathlib.Path((r"C:\Users\eoconne\Documents\Students_Colleagues\Alice\afm"
            r"\Pyjibe_implementation\Data_from_Chiaro"
            r"\AEBP1_01 Indentation_002.txt"))


    data = afmformats.load_data(path=path)[0]
    assert data["force"].size == 1644
    # maximum force is at end of 1st segment
    assert np.sum(data["segment"] == 0) == np.argmax(data["force"])+1


if __name__ == "__main__":
    # Run all tests
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
