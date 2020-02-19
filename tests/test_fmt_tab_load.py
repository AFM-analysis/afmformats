"""Test .tab format functionalities"""
import pathlib
import tempfile

import numpy as np

import afmformats


datadir = pathlib.Path(__file__).resolve().parent / "data"


def generate_tab_file():
    tf = tempfile.mktemp(suffix=".tab", prefix="afmformats_test_tab_")
    with open(tf, "w") as fd:
        fd.write("# force\ttip position\tsegment\r\n")
        for ii in range(100):
            fd.write("{}\t{}\t{}\r\n".format(ii*1e-9,
                                             np.pi*ii*1e-6,
                                             ii > 50))
    return tf


def test_open_simple():
    tf = generate_tab_file()
    data = afmformats.load_data(tf)[0]
    assert np.sum(data["segment"]) == 49
    assert np.allclose(data["force"][0], 0)
    assert np.allclose(data["force"][1], 1e-9)
    assert np.allclose(data["tip position"][1], np.pi*1e-6)
    # cleanup
    try:
        pathlib.Path(tf).unlink()
    except OSError:
        pass


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
