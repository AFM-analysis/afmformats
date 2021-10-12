"""Test AFM workshop format"""
import pathlib
import tempfile

import numpy as np
import pytest

import afmformats


data_path = pathlib.Path(__file__).resolve().parent / "data"


def test_map_grid():
    tf = data_path / "fmt-afm-workshop-fd_mapping_16_2018-08-01_13.07.zip"
    k = 20
    sens = .01e-6
    qmap = afmformats.AFMQMap(tf, meta_override={"spring constant": k,
                                                 "sensitivity": sens})
    assert qmap.shape == (4, 4)
    data1 = qmap.group[1]
    assert data1.metadata["grid size x"] == 2.533333333333333e-05
    assert data1.metadata["grid size y"] == 2.533333333333333e-05
    assert data1.metadata["grid index x"] == 1
    assert data1.metadata["grid index y"] == 0
    assert data1.metadata["position x"] == 7.333333333333332e-06
    assert data1.metadata["position y"] == 2e-6
    assert data1.metadata["grid shape x"] == 4
    assert data1.metadata["grid shape y"] == 4
    assert data1.metadata["grid center x"] == 1.05e-05
    assert data1.metadata["grid center y"] == 1.1499999999999998e-05


def test_map_open():
    tf = data_path / "fmt-afm-workshop-fd_mapping_16_2018-08-01_13.07.zip"
    k = 20
    sens = .01e-6
    data = afmformats.load_data(tf, meta_override={"spring constant": k,
                                                   "sensitivity": sens})
    assert len(data) == 16
    # these changes were made manually
    offset = 13761.9288
    for ii in range(len(data)):
        assert data[ii]["height (measured)"][0] == -(offset + ii) * 1e-9

    assert data[0]["height (measured)"][0] != data[1]["height (measured)"][0]
    assert np.allclose(data[0]["force"][0], 0.6875 * sens * k)


def test_missing_sens():
    tf = data_path / "fmt-afm-workshop-fd_single_2018-08-01_13.06.09.csv"
    try:
        afmformats.load_data(tf)
    except afmformats.errors.MissingMetaDataError:
        pass


def test_single_conversion():
    tf = data_path / "fmt-afm-workshop-fd_single_2018-08-01_13.06.09.csv"
    k = 20
    sens = .01e-6
    data = afmformats.load_data(tf, meta_override={"spring constant": k,
                                                   "sensitivity": sens})[0]
    assert data.metadata["spring constant"] == k
    assert "force" in data.columns
    assert np.allclose(data["force"][0], 0.6861 * sens * k)


def test_single_open():
    tf = data_path / "fmt-afm-workshop-fd_single_2020-02-14_13.41.25.csv"
    data = afmformats.load_data(tf)[0]
    assert "force" in data.columns
    assert np.allclose(data["force"][0], 1276.4373e-9)
    assert data.metadata["date"] == "2020-02-14"
    assert data.metadata["time"] == "13:41:26"


def test_single_open_issue_17():
    tf = data_path / "fmt-afm-workshop-fd_single_2021-01-15.csv"
    k = 20
    sens = .01e-6
    data = afmformats.load_data(tf, meta_override={"spring constant": k,
                                                   "sensitivity": sens})[0]
    assert "force" in data.columns
    assert np.allclose(data["force"][0], 1.6524e-07)
    assert data.metadata["spring constant"] == k
    assert data.metadata["software version"] == "4.0.0.62"
    assert data.metadata["date"] == "2021-01-15"
    assert data.metadata["time"] == "13:11:45"


def test_single_open_issue_17_no_or_invalid_metadata():
    tf = data_path / "fmt-afm-workshop-fd_single_2021-01-15.csv"
    with pytest.raises(afmformats.errors.MissingMetaDataError,
                       match="specify sensitivity and spring constant"):
        afmformats.load_data(tf)[0]


def test_single_open_issue_17_valid_metadata():
    tf = data_path / "fmt-afm-workshop-fd_single_2021-01-15.csv"
    tmpd = pathlib.Path(tempfile.mkdtemp("modified"))
    tf2 = tmpd / tf.name

    rawdata = tf.read_text()
    rawdata = rawdata.replace("Light Lever Gain, mV/nm:	1.000000",
                              "Light Lever Gain, mV/nm:	100")
    rawdata = rawdata.replace("Force Constant, nN/nm:	1.000000",
                              "Force Constant, nN/nm:	20.0")

    tf2.write_text(rawdata)

    data = afmformats.load_data(tf2)[0]

    assert "force" in data.columns
    assert data.metadata["spring constant"] == 20
    assert data.metadata["sensitivity"] == .01e-6


def test_single_open_with_precomputed_force():
    # This file contains force data in Newtons but no tip position.
    # afmformats should not request additional metadata, although
    # nanite may, because it needs it for the computation of the
    # tip position.
    tf = data_path / "fmt-afm-workshop-fd_single_2021-10-22_14.16.csv"
    data = afmformats.load_data(tf)[0]
    assert "tip position" not in data
    assert "force" in data
    assert "spring constant" not in data.metadata


if __name__ == "__main__":
    # Run all tests
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
