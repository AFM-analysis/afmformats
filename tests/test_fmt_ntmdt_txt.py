"""Test NT-MDT text export format"""
import pathlib

import numpy as np

import afmformats


datadir = pathlib.Path(__file__).resolve().parent / "data"


def test_open_simple():
    path = datadir / "2015_01_17_gel4-0,1_mQ_adh_6B_Curve_DFL_Height_51.txt"
    meta_override = {}
    meta_override["spring constant"] = 0.055
    meta_override["sensitivity"] = 61
    data = afmformats.load_data(path=path, meta_override=meta_override)[0]
    assert data["force"].size == 1644
    assert np.sum(~data["segment"]) == np.argmax(data["force"])+1


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
