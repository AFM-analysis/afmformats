import pathlib

import pytest

import afmformats


data_path = pathlib.Path(__file__).parent / "data"


# pass all available files
@pytest.mark.parametrize("path", afmformats.find_data(data_path))
def test_load_all_with_callback(path):
    """Make sure that the callback function is properly implemented"""
    calls = []

    def callback(value):
        calls.append(value)

    afmformats.load_data(path=path,
                         callback=callback,
                         meta_override={"spring constant": 20,
                                        "sensitivity": .01e-6})
    assert calls[-1] == 1
