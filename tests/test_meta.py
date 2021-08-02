"""MetaData class"""
import copy

import numpy as np

import afmformats.meta as am


def test_parse_time():
    assert am.parse_time("16:10:20") == "16:10:20"
    assert am.parse_time("6:1:2") == "06:01:02"
    assert am.parse_time("6:1:2 PM") == "18:01:02"
    assert am.parse_time("6:1:2.0 PM") == "18:01:02"
    assert am.parse_time("6:1:2.001 PM") == "18:01:02.001"
    assert am.parse_time("6:1:2.0010 PM") == "18:01:02.001"


def test_get_ids():
    md = am.MetaData({"date": "2020-04-01",
                      "time": "21:56:30",
                      "enum": "2"})
    assert md["session id"] == "2020-04-01_21:56:30"
    assert md["curve id"] == "2020-04-01_21:56:30_2"

    # override session
    md["session id"] = "peter"
    assert md["session id"] == "peter"
    assert md["curve id"] == "peter_2"

    # override curve
    md["curve id"] = "hans"
    assert md["curve id"] == "hans"


def test_lazy_metadata():
    md = am.MetaData({"enum": "2",
                      "z range": am.LazyMetaValue(np.abs, -3),
                      "imaging mode": "force-distance"})
    value1 = super(am.MetaData, md).__getitem__("z range")
    assert isinstance(value1, am.LazyMetaValue)
    value2 = md["z range"]
    assert not isinstance(value2, am.LazyMetaValue)
    assert value2 == 3
    # the LazyMetaValue should have been replaced with the value
    value3 = super(am.MetaData, md).__getitem__("z range")
    assert not isinstance(value3, am.LazyMetaValue)
    assert value3 == 3
    assert md["segment count"] == 2


def test_lazy_metadata_copy():
    md = am.MetaData({"enum": "2",
                      "z range": am.LazyMetaValue(np.abs, -3),
                      "imaging mode": "force-distance"})
    mdc = md.copy()
    value1 = super(am.MetaData, md).__getitem__("z range")
    value2 = super(am.MetaData, mdc).__getitem__("z range")
    assert isinstance(value1, am.LazyMetaValue)
    assert isinstance(value2, am.LazyMetaValue)
    assert value1 is value2, "LazyMetaValue should not be copied"
    # access it and make sure that LazyMetaValue is overridden in md
    assert md["z range"] == 3
    value3 = super(am.MetaData, md).__getitem__("z range")
    assert not isinstance(value3, am.LazyMetaValue)
    # for mdc, this should not have happened
    value4 = super(am.MetaData, mdc).__getitem__("z range")
    assert isinstance(value4, am.LazyMetaValue)
    # but the value should be set
    assert value4.value == 3


def test_lazy_metadata_deepcopy():
    md = am.MetaData({"enum": "2",
                      "z range": am.LazyMetaValue(np.abs, -3),
                      "imaging mode": "force-distance"})
    mdc = copy.deepcopy(md)
    value1 = super(am.MetaData, md).__getitem__("z range")
    value2 = super(am.MetaData, mdc).__getitem__("z range")
    assert isinstance(value1, am.LazyMetaValue)
    assert isinstance(value2, am.LazyMetaValue)
    assert value1 is value2, "LazyMetaValue should not be copied"
    # access it and make sure that LazyMetaValue is overridden in md
    assert md["z range"] == 3
    value3 = super(am.MetaData, md).__getitem__("z range")
    assert not isinstance(value3, am.LazyMetaValue)
    # for mdc, this should not have happened
    value4 = super(am.MetaData, mdc).__getitem__("z range")
    assert isinstance(value4, am.LazyMetaValue)
    # but the value should be set
    assert value4.value == 3


def test_values_with_lazy_meta():
    md = am.MetaData({"enum": "2",
                      "z range": am.LazyMetaValue(np.abs, -3)})
    assert list(md.values()) == ["2", 3]


if __name__ == "__main__":
    # Run all tests
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
