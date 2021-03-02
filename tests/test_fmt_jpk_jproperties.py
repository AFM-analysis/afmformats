"""Test of basic opening functionalities"""
import pathlib

import numpy as np

import afmformats
from afmformats.fmt_jpk import JPKReader


datadir = pathlib.Path(__file__).resolve().parent / "data"


def test_meta_extracted_map():
    jpkfile = datadir / "map2x2_extracted.jpk-force-map"
    md = afmformats.load_data(jpkfile)[0].metadata
    summary = md.get_summary()
    for sec in ["acquisition", "dataset", "setup", "storage", "qmap"]:
        for kk in summary[sec]:
            v = summary[sec][kk]
            if not isinstance(v, (str, pathlib.Path)):
                assert not np.isnan(v), "should not be nan: '{}'".format(kk)


def test_meta_extracted_map2():
    jpkfile = datadir / "map0d_extracted.jpk-force-map"
    md = afmformats.load_data(jpkfile)[0].metadata
    summary = md.get_summary()
    for sec in ["acquisition", "dataset", "setup", "storage", "qmap"]:
        for kk in summary[sec]:
            v = summary[sec][kk]
            if not isinstance(v, (str, pathlib.Path)):
                assert not np.isnan(v), "should not be nan: '{}'".format(kk)


def test_meta_extracted_single():
    jpkfile = datadir / "spot3-0192.jpk-force"
    md = afmformats.load_data(jpkfile)[0].metadata
    summary = md.get_summary()
    for sec in ["acquisition", "dataset", "setup", "storage"]:
        for kk in summary[sec]:
            v = summary[sec][kk]
            if not isinstance(v, (str, pathlib.Path)):
                assert not np.isnan(v), "should not be nan: '{}'".format(kk)


def test_meta_simple():
    jpkfilemap = datadir / "map0d_extracted.jpk-force-map"
    jpkr = JPKReader(jpkfilemap)
    jpkr.get_metadata(index=0, segment=0)


def test_meta_single():
    jpkfile = datadir / "spot3-0192.jpk-force"
    jpkr = JPKReader(jpkfile)
    md = jpkr.get_metadata(index=0, segment=0)
    assert md["imaging mode"] == "force-distance"
    assert md["duration"] == 0.9999999999999998


if __name__ == "__main__":
    # Run all tests
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
