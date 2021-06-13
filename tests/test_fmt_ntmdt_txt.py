"""Test NT-MDT text export format"""
import pathlib
import tempfile

import numpy as np
import pytest

import afmformats


datadir = pathlib.Path(__file__).resolve().parent / "data"


def test_detect():
    path = datadir / "2015_01_17_gel4-0,1_mQ_adh_6B_Curve_DFL_Height_51.txt"
    recipe = afmformats.formats.get_recipe(path)
    assert recipe.descr == "exported by NT-MDT Nova"


def test_detect_bad():
    path = datadir / "2015_01_17_gel4-0,1_mQ_adh_6B_Curve_DFL_Height_51.txt"
    _, tf = tempfile.mkstemp(suffix=".txt", prefix="afmformats_test")
    data = pathlib.Path(path).read_text()
    data.replace("\t", ",")
    with pathlib.Path(tf).open("w") as fd:
        # add a header line without any hashes
        fd.write("header without hash")
        fd.write(data)

    with pytest.raises(afmformats.errors.FileFormatNotSupportedError):
        afmformats.formats.get_recipe(tf)


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
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
