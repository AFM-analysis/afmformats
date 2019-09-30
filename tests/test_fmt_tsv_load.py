"""Test of basic opening functionalities"""
import pathlib
import tempfile

import numpy as np

import afmformats


def generate_tsv_file():
    tf = tempfile.mktemp(suffix=".tsv", prefix="afmformats_test_tsv_")
    with open(tf, "w") as fd:
        fd.write("# force\ttip position\tsegment\r\n")
        for ii in range(100):
            fd.write("{}\t{}\t{}\r\n".format(ii*1e-9,
                                             np.pi*ii*1e-6,
                                             ii>50))
    return tf


def test_open_simple():
    tf = generate_tsv_file()
    data = afmformats.load_data(tf)[0]
    assert np.sum(data["segment"]) == 49 
    assert np.allclose(data["force"][0], 0)
    assert np.allclose(data["force"][1], 1e-9)
    assert np.allclose(data["tip position"][1], np.pi*1e-6)


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
