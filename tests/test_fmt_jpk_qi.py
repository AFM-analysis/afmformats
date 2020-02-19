"""Test of basic opening functionalities"""
import pathlib

import numpy as np

import afmformats
from afmformats.fmt_jpk import read_jpk


datadir = pathlib.Path(__file__).resolve().parent / "data"


def test_open_jpk_qi():
    jpkfile = datadir / "2020.02.07-16.29.05.036.jpk-qi-data"
    data = read_jpk.load_jpk(jpkfile)
    force = data[0][0][0]["force"]
    height = data[0][0][0]["height (measured)"]
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
    data = read_jpk.load_jpk(jpkfile)
    assert len(data) == 4
    assert data[0][0][1]["grid index x"] == 0
    assert data[1][0][1]["grid index x"] == 1
    assert data[1][0][1]["grid index y"] == 0
    assert data[2][0][1]["grid index x"] == 2
    assert data[3][0][1]["grid index x"] == 3
    assert data[3][0][1]["grid index x"] == data[3][1][1]["grid index x"]
    assert data[3][0][1]["instrument"] == "JPK01496-H-18-0132"
    assert data[3][0][1]["software version"] == "6.1.157"


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
