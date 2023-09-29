"""Test of basic opening functionalities"""
import pathlib

import numpy as np
import pytest


import afmformats.errors
from afmformats.formats.fmt_jpk import jpk_data, load_jpk
from afmformats.formats.fmt_jpk.jpk_reader import ArchiveCache, JPKReader


data_path = pathlib.Path(__file__).resolve().parent / "data"


def test_open_jpk_simple():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    jpkr = JPKReader(jpkfile)
    p_seg = jpkr.get_index_segment_path(0, 0)
    loc_list = [ff for ff in jpkr.files if ff.count(p_seg)]
    name, slot, dat = jpk_data.find_column_dat(loc_list, "height (piezo)")
    properties = jpkr._get_index_segment_properties(0, 0)
    arc = ArchiveCache.get(jpkr.path)
    with arc.open(dat, "r") as fd:
        height = jpk_data.load_dat_raw(fd, name=name,
                                       properties=properties)
    assert height[0] == 50.425720226584403


def test_open_jpk_calibration():
    cf = data_path / \
         "fmt-jpk-cl_calibration_force-save-2015.02.04-11.25.21.294.jpk-force"

    with pytest.raises(afmformats.errors.MissingMetaDataError,
                       match="sensitivity"):
        load_jpk(cf)


def test_open_jpk_conversion():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    jpkr = JPKReader(jpkfile)
    p_seg = jpkr.get_index_segment_path(0, 0)
    loc_list = [ff for ff in jpkr.files if ff.count(p_seg)]
    properties = jpkr._get_index_segment_properties(0, 0)
    chan_data = {}
    for column in ["force", "height (piezo)", "height (measured)"]:
        name, slot, dat = jpk_data.find_column_dat(loc_list, column)
        arc = ArchiveCache.get(jpkr.path)
        with arc.open(dat, "r") as fd:
            chan_data[name] = jpk_data.load_dat_unit(fd, name, properties,
                                                     slot)
    assert chan_data["vDeflection"][2] == "vDeflection (Force)"
    assert chan_data["vDeflection"][1] == "N"
    assert chan_data["vDeflection"][0][0] == -5.145579192349918e-10
    assert chan_data["height"][0][0] == 2.8783223430683289e-05
    assert chan_data["strainGaugeHeight"][0][0] == 2.2815672438768612e-05


def test_get_both_metadata():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    jpkr = JPKReader(jpkfile)
    md1 = jpkr.get_metadata(index=0, segment=0)
    md2 = jpkr.get_metadata(index=0, segment=1)
    md = jpkr.get_metadata(index=0, segment=None)
    for key1 in md1:
        if key1 in ["duration", "point count"]:
            assert md1[key1] != md[key1], key1
        else:
            assert md1[key1] == md[key1], key1
    for key2 in md2:
        if key2 in ["duration", "point count", "time"]:
            # time from approach curve should be used
            assert md2[key2] != md[key2], key2
        else:
            assert md2[key2] == md[key2], key2


def test_get_single_curves():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    jpkr = JPKReader(jpkfile)
    jpkr.get_data(column="force", index=0, segment=0)
    jpkr.get_data(column="height (piezo)", index=0, segment=0)
    jpkr.get_data(column="height (measured)", index=0, segment=0)


def test_get_time():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    jpkr = JPKReader(jpkfile)
    time1 = jpkr.get_data(column="time", index=0, segment=0)
    time2 = jpkr.get_data(column="time", index=0, segment=1)
    m1 = jpkr.get_metadata(0, 0)
    m2 = jpkr.get_metadata(0, 1)
    assert np.allclose(m1["duration"], time2[0])
    assert len(time1) == m1["point count"]
    assert len(time2) == m2["point count"]
    assert np.all(time1 < m1["duration"])
    assert np.all(time2 < (m1["duration"] + m2["duration"]))
    md = jpkr.get_metadata(0)
    assert md["duration"] == m1["duration"] + m2["duration"]
    assert md["point count"] == m1["point count"] + m2["point count"]


def test_get_single_custom_slot():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    jpkr = JPKReader(jpkfile)
    p_seg = jpkr.get_index_segment_path(0, 0)
    loc_list = [ff for ff in jpkr.files if ff.count(p_seg)]
    name, slot, dat = jpk_data.find_column_dat(loc_list, "height (piezo)")
    properties = jpkr._get_index_segment_properties(0, 0)
    arc = ArchiveCache.get(jpkr.path)
    with arc.open(dat, "r") as fd:
        data, unit, _ = jpk_data.load_dat_unit(fd, name=name,
                                               properties=properties,
                                               slot="nominal")
    assert data[0] == 4.9574279773415606e-05


def test_meta():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    jpkr = JPKReader(jpkfile)
    md = jpkr.get_metadata(0, 1)
    assert md["spring constant"] == 0.043493666407368466


def test_meta_missing():
    jpkfile = data_path / "fmt-jpk-fd_single-modified_2023.jpk-force"

    with pytest.raises(afmformats.errors.MissingMetaDataError,
                       match="spring constant"):
        load_jpk(jpkfile)

    data_list = load_jpk(jpkfile,
                         meta_override={"spring constant": 12})
    meta = data_list[0]["metadata"]
    assert meta["spring constant"] == 12


def test_meta_override_multiple_times():
    jpkfile = data_path / "fmt-jpk-fd_single-modified_2023.jpk-force"
    jpkr = JPKReader(jpkfile)

    with pytest.raises(afmformats.errors.MissingMetaDataError,
                       match="spring constant"):
        jpkr.get_metadata(index=0)

    jpkr.set_metadata({"spring constant": 10})
    assert jpkr.get_metadata(index=0)["spring constant"] == 10

    jpkr.set_metadata({"spring constant": 12})
    assert jpkr.get_metadata(index=0)["spring constant"] == 12


def test_load_jpk():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    jpkr = JPKReader(jpkfile)
    md = jpkr.get_metadata(0, 1)
    assert md["imaging mode"] == "force-distance"
    assert len(jpkr) == 1, "Only one measurement"
    assert len(jpkr.get_index_segment_numbers(0)) == 2, "approach and retract"
