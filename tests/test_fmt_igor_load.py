"""Test Asylum .ibw format"""
import pathlib

import numpy as np

import afmformats


datadir = pathlib.Path(__file__).resolve().parent / "data"


def test_open_with_metadata():
    jpkfile = datadir / "U3_3_p10004.ibw"
    fdat = afmformats.load_data(jpkfile, mode="force-distance")[0]
    for col in ['force', 'height (measured)', 'height (piezo)', 'segment']:
        assert col in fdat
    assert fdat.metadata["sensitivity"] == 2.0364e-07
    assert fdat.metadata["spring constant"] == 0.31451
    assert fdat.metadata["setpoint"] == 1.8e-07
    assert np.allclose(fdat["force"].max(), 1.778407e-07, rtol=1e-7, atol=0)
    assert fdat.metadata["point count"] == 10097
    assert fdat.metadata["time"] == '18:18:49'
    assert np.allclose(fdat["height (measured)"].min(), -1.0322237e-06,
                       rtol=1e-7, atol=0)


def test_open_issue_8():
    # test file provided by María Tenorio (CC0)
    jpkfile = datadir / "SiN_FD_plot.ibw"
    fdat = afmformats.load_data(jpkfile, mode="force-distance")[0]
    assert fdat.metadata["time"] == "10:47:31"


if __name__ == "__main__":
    # Run all tests
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
