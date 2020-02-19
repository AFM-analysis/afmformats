"""Test .tab format functionalities"""
import pathlib
import tempfile

import numpy as np

import afmformats


datadir = pathlib.Path(__file__).resolve().parent / "data"


def test_save_open_with_metadata():
    jpkfile = datadir / "spot3-0192.jpk-force"
    fdat = afmformats.load_data(jpkfile, mode="force-distance")[0]
    _, path = tempfile.mkstemp(suffix=".h5", prefix="afmformats_test_")
    fdat.export(path, metadata=True, fmt="hdf5")
    fdat2 = afmformats.load_data(path, mode="force-distance")[0]
    # compare metadata
    for key in fdat.metadata:
        if key in ["path", "format"]:
            assert fdat.metadata[key] != fdat2.metadata[key]
        else:
            assert fdat.metadata[key] == fdat2.metadata[key]
    for col in fdat.columns:
        assert np.allclose(fdat[col], fdat2[col], atol=0)
    # cleanup
    try:
        pathlib.Path(path).unlink()
    except OSError:
        pass


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
