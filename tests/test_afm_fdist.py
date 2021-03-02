"""Test .h5 format writing"""
import pathlib
import tempfile

import h5py

import afmformats


datadir = pathlib.Path(__file__).resolve().parent / "data"


def test_export_hdf5():
    """Test for hotfixes in 0.7.1"""
    jpkfile = datadir / "spot3-0192.jpk-force"
    fdat = afmformats.load_data(jpkfile, mode="force-distance")[0]
    _, path = tempfile.mkstemp(suffix=".h5", prefix="afmformats_test_")

    with h5py.File(path, "w") as h5:
        fdat.export(h5, metadata=True, fmt="hdf5")
        fdat.export(h5, metadata=True, fmt="hdf5")

    with h5py.File(path, "r") as h5:
        assert h5["0"].attrs["enum"] == 0
        assert h5["1"].attrs["enum"] == 1
        assert h5["0"]["force"].attrs["unit"] == "N"


if __name__ == "__main__":
    # Run all tests
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
