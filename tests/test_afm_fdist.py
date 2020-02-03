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
