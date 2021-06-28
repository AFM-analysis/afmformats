import pathlib
import tempfile

import h5py
import numpy as np

import afmformats


data_dir = pathlib.Path(__file__).resolve().parent / "data"


def test_export_hdf5():
    """Test for hotfixes in 0.7.1"""
    jpkfile = data_dir / "spot3-0192.jpk-force"
    fdat = afmformats.load_data(jpkfile, modality="force-distance")[0]
    _, path = tempfile.mkstemp(suffix=".h5", prefix="afmformats_test_")

    with h5py.File(path, "w") as h5:
        fdat.export_data(h5, metadata=True, fmt="hdf5")
        fdat.export_data(h5, metadata=True, fmt="hdf5")

    with h5py.File(path, "r") as h5:
        assert h5["0"].attrs["enum"] == 0
        assert h5["1"].attrs["enum"] == 1
        assert h5["0"]["force"].attrs["unit"] == "N"


def test_load_custom_class():
    class TESTAFMData(afmformats.AFMForceDistance):
        pass
    jpkfile = data_dir / "spot3-0192.jpk-force"
    fdat = afmformats.load_data(jpkfile,
                                modality="force-distance",
                                data_classes_by_modality={
                                    "force-distance": TESTAFMData
                                }
                                )[0]
    assert isinstance(fdat, TESTAFMData)


def test_segment():
    jpkfile = data_dir / "spot3-0192.jpk-force"
    fdat = afmformats.load_data(jpkfile, modality="force-distance")[0]

    s1 = fdat.appr["segment"]
    assert np.all(s1 == 0)

    s2 = fdat.retr["segment"]
    assert np.all(s2 == 1)


if __name__ == "__main__":
    # Run all tests
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
