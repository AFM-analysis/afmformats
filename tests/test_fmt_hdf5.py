"""Test .tab format functionalities"""
import pathlib
import tempfile

import numpy as np

import afmformats


data_path = pathlib.Path(__file__).resolve().parent / "data"


def test_open_0_13_3():
    fdat = afmformats.load_data(data_path / "fmt-hdf5-fd_version_0.13.3.h5")[0]
    assert fdat.metadata["imaging mode"] == "force-distance"
    assert fdat["force"][2000] == -7.038311459845539e-10


def test_hdf5_metadata_contains():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    fdat = afmformats.load_data(jpkfile, modality="force-distance")[0]
    _, path = tempfile.mkstemp(suffix=".h5", prefix="afmformats_test_")
    fdat.export_data(path, metadata=True, fmt="hdf5")
    fdat2 = afmformats.load_data(path, modality="force-distance")[0]
    assert "force" in fdat2


def test_save_open_with_metadata():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    fdat = afmformats.load_data(jpkfile, modality="force-distance")[0]
    _, path = tempfile.mkstemp(suffix=".h5", prefix="afmformats_test_")
    fdat.export_data(path, metadata=True, fmt="hdf5")
    fdat2 = afmformats.load_data(path, modality="force-distance")[0]
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
