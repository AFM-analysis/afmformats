"""Test of basic opening functionalities"""
import pathlib

import numpy as np

import afmformats
from afmformats.fmt_jpk import load_jpk


datadir = pathlib.Path(__file__).resolve().parent / "data"


def test_open_jpk_map():
    jpkfile = datadir / "map0d_extracted.jpk-force-map"
    dataset = load_jpk(jpkfile)
    data = dataset[0]["data"]
    force = data["force"]
    height = data["height (measured)"]
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
    dataset = load_jpk(jpkfile)
    data = dataset[2]["data"]
    force = data["force"]
    height = data["height (measured)"]
    assert len(dataset) == 4
    assert np.allclose(force[0], -5.8540192943834714e-10)
    assert np.allclose(height[0], 0.0001001727719556085)
    assert dataset[0]["metadata"]["grid index x"] == 0
    assert dataset[1]["metadata"]["grid index x"] == 9
    assert dataset[2]["metadata"]["grid index x"] == 9
    assert dataset[3]["metadata"]["grid index x"] == 0


if __name__ == "__main__":
    # Run all tests
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
