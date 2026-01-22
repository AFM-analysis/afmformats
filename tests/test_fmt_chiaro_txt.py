"""Test Chiaro text export format"""
import pathlib
import zipfile
import tempfile
import numpy as np

import afmformats


def _load_zip_data_path():
    """Convenience function to find zipped test data path"""
    zpath = (pathlib.Path(__file__).resolve().parent / "data" /
             "fmt-chiaro-txt_AEBP1_Indentation_002.zip")
    # unpack
    arc = zipfile.ZipFile(str(zpath))
    # extract all files to a temporary directory
    edest = tempfile.mkdtemp(prefix=zpath.name)
    arc.extractall(edest)
    zip_temp_path = pathlib.Path(edest)
    data_paths = [r for r in zip_temp_path.rglob("*.txt") if r.is_file()]
    data_path = data_paths[0]
    return data_path


data_path = _load_zip_data_path()


def test_chairo_txt_open_check_data():
    data = afmformats.load_data(data_path)[0]
    assert data.metadata["imaging mode"] == "force-distance"
    assert data["force"][2000] == 9.399999999999999e-11


def test_chairo_txt_detect():
    recipe = afmformats.formats.get_recipe(data_path)
    assert recipe.descr == "exported by Optics11 Chiaro Indenter"
    assert recipe.maker == "Optics11 Life"


def test_chairo_txt_data_columns():
    data = afmformats.load_data(data_path)[0]

    assert "force" in data
    assert "height (piezo)" in data
    assert "height (measured)" in data
    assert "time" in data
    assert "segment" in data
    assert "tip position" in data  # already calculated when loaded


def test_chairo_txt_metadata():
    data = afmformats.load_data(data_path)[0]

    metadata = data.metadata
    avail_keys = ["date", "duration", "spring constant", "time",
                  "speed approach", "speed retract", "segment count"]
    for key in avail_keys:
        assert key in metadata


def test_chiaro_txt_segments():
    data = afmformats.load_data(data_path)[0]

    assert data["force"].size == 13827
    # maximum force is at end of 1st segment
    assert np.sum(data["segment"] == 0) == np.argmax(data["force"]) + 1


if __name__ == "__main__":
    # Run all tests
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
