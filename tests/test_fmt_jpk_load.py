"""Test of basic opening functionalities"""
import pathlib

import numpy as np

import afmformats


datadir = pathlib.Path(__file__).resolve().parent / "data"


def test_load_jpk_map():
    jpkfile = datadir / "map2x2_extracted.jpk-force-map"
    afmlist = afmformats.load_data(path=jpkfile)

    assert len(afmlist) == 4
    ds = afmlist[2]
    assert ds.metadata["index"] == 2
    # Verified with visual inspection of force curve in JPK software
    assert np.allclose(ds["force"][0], -5.8540192943834714e-10)
    assert np.allclose(ds["height (measured)"][0], 0.0001001727719556085)


def test_load_jpk_simple():
    jpkfile = datadir / "spot3-0192.jpk-force"
    afmlist = afmformats.load_data(path=jpkfile)
    ds = afmlist[0]
    assert ds.metadata["index"] == 0
    assert np.allclose(ds["height (measured)"][0], 2.2815672438768612e-05)


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
