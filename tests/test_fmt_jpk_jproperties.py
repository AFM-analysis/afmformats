"""Test of basic opening functionalities"""
import pathlib
import shutil

from afmformats.fmt_jpk import read_jpk_meta


datadir = pathlib.Path(__file__).resolve().parent / "data"


def test_meta_simple():
    jpkfilemap = datadir / "map0d_extracted.jpk-force-map"
    tdir = read_jpk_meta.extract_jpk(jpkfilemap)
    hpfile = tdir / "index/0/segments/0/segment-header.properties"
    read_jpk_meta.get_seg_head_prop(hpfile)
    shutil.rmtree(tdir, ignore_errors=True)


def test_mata_single():
    jpkfile = datadir / "spot3-0192.jpk-force"
    md = read_jpk_meta.get_meta_data(jpkfile)
    assert md["curve type"] == "extend-retract"
    assert md["duration [s]"] == 0.9999999999999998


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
