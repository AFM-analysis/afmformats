"""Test of basic opening functionalities"""
import pathlib

import numpy as np

import afmformats
from afmformats.fmt_jpk import read_jpk


datadir = pathlib.Path(__file__).resolve().parent / "data"


def test_open_jpk_map():
    jpkfile = datadir / "map0d_extracted.jpk-force-map"
    data = read_jpk.load_jpk(jpkfile)
    force = data[0][0][0]["force"]
    height = data[0][0][0]["height (measured)"]
    # Verified with visual inspection of force curve in JPK software
    assert np.allclose(force[0], -4.7426862623854873e-10)
    assert np.allclose(height[0], 7.0554296897149161e-05)


def test_open_jpk_map_enum():
    jpkfile = datadir / "map2x2_extracted.jpk-force-map"
    data = afmformats.load_data(jpkfile)
    # Correct enumeration
    assert data[0].metadata["enum"] == 0
    assert data[1].metadata["enum"] == 1
    assert data[2].metadata["enum"] == 2
    assert data[3].metadata["enum"] == 3


def test_open_jpk_map2():
    jpkfile = datadir / "map2x2_extracted.jpk-force-map"
    data = read_jpk.load_jpk(jpkfile)
    force = data[2][0][0]["force"]
    height = data[2][0][0]["height (measured)"]
    assert len(data) == 4
    assert np.allclose(force[0], -5.8540192943834714e-10)
    assert np.allclose(height[0], 0.0001001727719556085)
    assert data[0][0][1]["grid index x"] == 0
    assert data[1][0][1]["grid index x"] == 9
    assert data[2][0][1]["grid index x"] == 9
    assert data[3][0][1]["grid index x"] == 0
    assert data[3][0][1]["grid index x"] == data[3][1][1]["grid index x"]


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
