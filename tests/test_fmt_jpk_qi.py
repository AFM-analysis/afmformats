"""Test of basic opening functionalities"""
import pathlib

import numpy as np

import afmformats
from afmformats.fmt_jpk import load_jpk


datadir = pathlib.Path(__file__).resolve().parent / "data"


def test_open_jpk_qi():
    jpkfile = datadir / "2020.02.07-16.29.05.036.jpk-qi-data"
    dataset = load_jpk(jpkfile)
    data = dataset[0]["data"]
    force = data["force"]
    height = data["height (measured)"]
    # Verified with visual inspection of force curve in JPK software
    assert np.allclose(force[0], -1.269014596090597e-10)
    assert np.allclose(height[0], 4.716154783699957e-06)


def test_open_jpk_map_enum():
    jpkfile = datadir / "2020.02.07-16.29.05.036.jpk-qi-data"
    data = afmformats.load_data(jpkfile)
    # Correct enumeration
    assert data[0].metadata["enum"] == 0
    assert data[1].metadata["enum"] == 1
    assert data[2].metadata["enum"] == 2
    assert data[3].metadata["enum"] == 3


def test_open_jpk_map2():
    jpkfile = datadir / "2020.02.07-16.29.05.036.jpk-qi-data"
    dataset = load_jpk(jpkfile)
    assert len(dataset) == 4
    assert dataset[0]["metadata"]["grid index x"] == 0
    assert dataset[1]["metadata"]["grid index x"] == 1
    assert dataset[1]["metadata"]["grid index y"] == 0
    assert dataset[2]["metadata"]["grid index x"] == 2
    assert dataset[3]["metadata"]["grid index x"] == 3
    assert dataset[3]["metadata"]["instrument"] == "JPK01496-H-18-0132"
    assert dataset[3]["metadata"]["software version"] == "6.1.157"


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
