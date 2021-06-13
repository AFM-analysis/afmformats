"""Test .tab format functionalities"""
import pathlib
import tempfile

import numpy as np
import pytest

import afmformats


datadir = pathlib.Path(__file__).resolve().parent / "data"


def generate_tab_file():
    tf = tempfile.mktemp(suffix=".tab", prefix="afmformats_test_tab_")
    with open(tf, "w") as fd:
        fd.write('# BEGIN METADATA\r\n')
        fd.write('# {\r\n')
        fd.write('#   "curve id": "2016.06.15-10.18.28-00093:6",\r\n')
        fd.write('#   "date": "2016-06-15",\r\n')
        fd.write('#   "duration": 4.2,\r\n')
        fd.write('#   "enum": 0,\r\n')
        fd.write('#   "feedback mode": "contact",\r\n')
        fd.write('#   "format": "JPK Instruments (binary FD data)",\r\n')
        fd.write('#   "imaging mode": "force-distance",\r\n')
        fd.write('#   "instrument": "JPK00758-CellHesion-200",\r\n')
        fd.write('#   "point count": 8400,\r\n')
        fd.write('#   "position x": -0.0021247991071428572,\r\n')
        fd.write('#   "position y": -0.0025797712053571434,\r\n')
        fd.write('#   "rate approach": 2000.0,\r\n')
        fd.write('#   "rate retract": 2000.0,\r\n')
        fd.write('#   "sensitivity": 9.120708714532604e-08,\r\n')
        fd.write('#   "session id": "2016.06.15-10.18.28-00093",\r\n')
        fd.write('#   "setpoint": 6.000000000000001e-09,\r\n')
        fd.write('#   "software": "JPK",\r\n')
        fd.write('#   "software version": "5.0.76",\r\n')
        fd.write('#   "speed approach": 9.999999999999999e-06,\r\n')
        fd.write('#   "speed retract": 2.4999999999999998e-05,\r\n')
        fd.write('#   "spring constant": 0.02230065831827453,\r\n')
        fd.write('#   "time": "15:52:13.937",\r\n')
        fd.write('#   "z range": 2.6486991447509974e-05\r\n')
        fd.write('# }\r\n')
        fd.write('# END METADATA\r\n')
        fd.write('# force\ttip position\tsegment\r\n')
        for ii in range(100):
            fd.write("{}\t{}\t{}\r\n".format(ii*1e-9,
                                             np.pi*ii*1e-6,
                                             ii > 50))
    return tf


def test_detect():
    tf = generate_tab_file()
    recipe = afmformats.formats.get_recipe(tf)
    assert recipe.descr == "tab-separated values"


def test_detect_bad():
    _, tf = tempfile.mkstemp(suffix=".tab", prefix="afmformats_test")

    with pytest.raises(afmformats.errors.FileFormatNotSupportedError):
        afmformats.formats.get_recipe(tf)


def test_open_simple():
    tf = generate_tab_file()
    data = afmformats.load_data(tf)[0]
    assert np.sum(data["segment"]) == 49
    assert np.allclose(data["force"][0], 0)
    assert np.allclose(data["force"][1], 1e-9)
    assert np.allclose(data["tip position"][1], np.pi*1e-6)


def test_save_open_with_metadata():
    jpkfile = datadir / "spot3-0192.jpk-force"
    fdat = afmformats.load_data(jpkfile, mode="force-distance")[0]
    _, path = tempfile.mkstemp(suffix=".tab", prefix="afmformats_test_")
    fdat.export(path, metadata=True, fmt="tab")
    fdat2 = afmformats.load_data(path, mode="force-distance")[0]
    # compare metadata
    for key in fdat.metadata:
        if key in ["path", "format"]:
            assert fdat.metadata[key] != fdat2.metadata[key]
        else:
            assert fdat.metadata[key] == fdat2.metadata[key]
    for col in fdat.columns:
        assert np.allclose(fdat[col], fdat2[col], atol=0)


if __name__ == "__main__":
    # Run all tests
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
