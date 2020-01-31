"""Test of basic opening functionalities"""
import pathlib
import shutil

import numpy as np

import afmformats
from afmformats.fmt_jpk import read_jpk_meta


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
    tdir = read_jpk_meta.extract_jpk(jpkfilemap)
    hpfile = tdir / "index/0/segments/0/segment-header.properties"
    read_jpk_meta.get_seg_head_prop(hpfile)
    shutil.rmtree(tdir, ignore_errors=True)


def test_meta_single():
    jpkfile = datadir / "spot3-0192.jpk-force"
    tdir = read_jpk_meta.extract_jpk(jpkfile)
    sdir = tdir / "segments" / "0"
    md = read_jpk_meta.get_meta_data_seg(sdir)
    assert md["imaging mode"] == "force-distance"
    assert md["duration"] == 0.9999999999999998
    shutil.rmtree(tdir, ignore_errors=True)


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
