import pathlib
import tempfile

import h5py
import numpy as np

import afmformats


data_path = pathlib.Path(__file__).resolve().parent / "data"


def test_data_content():
    jpkfile = data_path / "fmt-jpk-sr_cell1-0008.jpk-force"
    fdat = afmformats.load_data(jpkfile)[0]

    assert np.allclose(np.mean(fdat.prep["force"]), -1.1667527118459774e-07,
                       atol=0, rtol=1e-12)
    assert np.allclose(np.mean(fdat.appr["force"]), 1.2185861117864535e-08,
                       atol=0, rtol=1e-12)
    assert np.allclose(np.mean(fdat.intr["force"]), 2.3613889957445826e-08,
                       atol=0, rtol=1e-12)
    assert np.allclose(np.mean(fdat.retr["force"]), -1.4864363676098427e-07,
                       atol=0, rtol=1e-12)

    assert np.allclose(np.mean(fdat.prep["time"]), 0.498046875,
                       atol=0, rtol=1e-12)
    assert np.allclose(np.mean(fdat.appr["time"]), 1.499755859375,
                       atol=0, rtol=1e-12)
    assert np.allclose(np.mean(fdat.intr["time"]), 16.998046875,
                       atol=0, rtol=1e-12)
    assert np.allclose(np.mean(fdat.retr["time"]), 32.47607421875,
                       atol=0, rtol=1e-12)

    assert np.allclose(np.mean(fdat.retr["time"][20]), 32.009765625,
                       atol=0, rtol=1e-12)
    assert np.allclose(np.mean(fdat.appr["force"][1]), -1.1663463779185065e-07,
                       atol=0, rtol=1e-12)


def test_export_hdf5():
    jpkfile = data_path / "fmt-jpk-sr_cell1-0008.jpk-force"
    fdat = afmformats.load_data(jpkfile, modality="stress-relaxation")[0]
    _, path = tempfile.mkstemp(suffix=".h5", prefix="afmformats_test_")

    with h5py.File(path, "w") as h5:
        fdat.export_data(h5, metadata=True, fmt="hdf5")
        fdat.export_data(h5, metadata=True, fmt="hdf5")

    with h5py.File(path, "r") as h5:
        assert h5["0"].attrs["enum"] == 0
        assert h5["1"].attrs["enum"] == 1
        assert h5["0"]["force"].attrs["unit"] == "N"
        assert h5["0"].attrs["imaging mode"] == "stress-relaxation"


def test_load_custom_class():
    class TESTAFMData(afmformats.AFMStressRelaxation):
        pass
    jpkfile = data_path / "fmt-jpk-sr_cell1-0008.jpk-force"
    fdat = afmformats.load_data(jpkfile,
                                modality="stress-relaxation",
                                data_classes_by_modality={
                                    "stress-relaxation": TESTAFMData
                                }
                                )[0]
    assert isinstance(fdat, TESTAFMData)


def test_segment():
    jpkfile = data_path / "fmt-jpk-sr_cell1-0008.jpk-force"
    fdat = afmformats.load_data(jpkfile, modality="stress-relaxation")[0]

    s0 = fdat.prep["segment"]
    assert np.all(s0 == 0)

    s1 = fdat.appr["segment"]
    assert np.all(s1 == 1)

    s2 = fdat.intr["segment"]
    assert np.all(s2 == 2)

    s2 = fdat.retr["segment"]
    assert np.all(s2 == 3)
