"""MetaData class"""
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


if __name__ == "__main__":
    # Run all tests
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
