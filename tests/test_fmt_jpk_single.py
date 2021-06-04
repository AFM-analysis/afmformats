"""Test of basic opening functionalities"""
import pathlib

import numpy as np

from afmformats.fmt_jpk import jpk_data, jpk_meta, JPKReader, load_jpk


datadir = pathlib.Path(__file__).resolve().parent / "data"


def test_open_jpk_simple():
    jpkfile = datadir / "spot3-0192.jpk-force"
    jpkr = JPKReader(jpkfile)
    p_seg = jpkr.get_index_segment_path(0, 0)
    loc_list = [ff for ff in jpkr.files if ff.count(p_seg)]
    name, slot, dat = jpk_data.find_column_dat(loc_list, "height (piezo)")
    properties = jpkr._get_index_segment_properties(0, 0)
    with jpkr.get_archive() as arc:
        with arc.open(dat, "r") as fd:
            height = jpk_data.load_dat_raw(fd, name=name,
                                           properties=properties)
    assert height[0] == 50.425720226584403


def test_open_jpk_calibration():
    cf = datadir / "calibration_force-save-2015.02.04-11.25.21.294.jpk-force"
    try:
        load_jpk(cf)
    except jpk_meta.ReadJPKMetaKeyError:
        pass
    else:
        assert False, "no spring constant should raise error"


def test_open_jpk_conversion():
    jpkfile = datadir / "spot3-0192.jpk-force"
    jpkr = JPKReader(jpkfile)
    p_seg = jpkr.get_index_segment_path(0, 0)
    loc_list = [ff for ff in jpkr.files if ff.count(p_seg)]
    properties = jpkr._get_index_segment_properties(0, 0)
    chan_data = {}
    for column in ["force", "height (piezo)", "height (measured)"]:
        name, slot, dat = jpk_data.find_column_dat(loc_list, column)
        with jpkr.get_archive() as arc:
            with arc.open(dat, "r") as fd:
                chan_data[name] = jpk_data.load_dat_unit(fd, name, properties,
                                                         slot)
    assert chan_data["vDeflection"][2] == "vDeflection (Force)"
    assert chan_data["vDeflection"][1] == "N"
    assert chan_data["vDeflection"][0][0] == -5.145579192349918e-10
    assert chan_data["height"][0][0] == 2.8783223430683289e-05
    assert chan_data["strainGaugeHeight"][0][0] == 2.2815672438768612e-05


def test_get_both_metadata():
    jpkfile = datadir / "spot3-0192.jpk-force"
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
    jpkfile = datadir / "spot3-0192.jpk-force"
    jpkr = JPKReader(jpkfile)
    jpkr.get_data(column="force", index=0, segment=0)
    jpkr.get_data(column="height (piezo)", index=0, segment=0)
    jpkr.get_data(column="height (measured)", index=0, segment=0)


def test_get_time():
    jpkfile = datadir / "spot3-0192.jpk-force"
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
    jpkfile = datadir / "spot3-0192.jpk-force"
    jpkr = JPKReader(jpkfile)
    p_seg = jpkr.get_index_segment_path(0, 0)
    loc_list = [ff for ff in jpkr.files if ff.count(p_seg)]
    name, slot, dat = jpk_data.find_column_dat(loc_list, "height (piezo)")
    properties = jpkr._get_index_segment_properties(0, 0)
    with jpkr.get_archive() as arc:
        with arc.open(dat, "r") as fd:
            data, unit, _ = jpk_data.load_dat_unit(fd, name=name,
                                                   properties=properties,
                                                   slot="nominal")
    assert data[0] == 4.9574279773415606e-05


def test_meta():
    jpkfile = datadir / "spot3-0192.jpk-force"
    jpkr = JPKReader(jpkfile)
    md = jpkr.get_metadata(0, 1)
    assert md["spring constant"] == 0.043493666407368466


def test_load_jpk():
    jpkfile = datadir / "spot3-0192.jpk-force"
    jpkr = JPKReader(jpkfile)
    md = jpkr.get_metadata(0, 1)
    assert md["imaging mode"] == "force-distance"
    assert len(jpkr) == 1, "Only one measurement"
    assert len(jpkr.get_index_segment_numbers(0)) == 2, "approach and retract"


if __name__ == "__main__":
    # Run all tests
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
