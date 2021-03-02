"""Test AFM workshop format"""
import pathlib

import numpy as np

import afmformats


datadir = pathlib.Path(__file__).resolve().parent / "data"


def test_missing_sens():
    tf = datadir / "AFM-workshop_FD_single_2018-08-01_13.06.09.csv"
    try:
        afmformats.load_data(tf)
    except afmformats.errors.MissingMetaDataError:
        pass


def test_open_conversion():
    tf = datadir / "AFM-workshop_FD_single_2018-08-01_13.06.09.csv"
    k = 20
    sens = .01e-6
    data = afmformats.load_data(tf, meta_override={"spring constant": k,
                                                   "sensitivity": sens})[0]
    assert data.metadata["spring constant"] == k
    assert "force" in data.columns
    assert np.allclose(data["force"][0], 0.6861 * sens * k)


def test_open_force():
    tf = datadir / "AFM-workshop_FD_single_2020-02-14_13.41.25.csv"
    data = afmformats.load_data(tf)[0]
    assert "force" in data.columns
    assert np.allclose(data["force"][0], 1276.4373e-9)


if __name__ == "__main__":
    # Run all tests
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
