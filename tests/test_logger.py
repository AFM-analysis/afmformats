import pathlib
import pytest

import afmformats

data_path = pathlib.Path(__file__).resolve().parent / "data"


def test_logger_load_data_success():
    path = data_path / "fmt-tab-fd_version_0.13.3.tab"
    log_path = pathlib.Path(afmformats.DEFAULT_LOG_PATH)

    afmdata = afmformats.load_data(path)
    assert len(afmdata) == 1

    with log_path.open(encoding="utf-8") as fd:
        new_output = fd.read()

    assert "afmformats logging initialized" in new_output
    assert "Loaded 1 dataset(s)" in new_output
    assert str(path) in new_output
    assert "tab-separated values" in new_output


@pytest.mark.parametrize(
    "file_name",
    ["fmt-tab-fd_version_0.13.3.slab"])
def test_logger_load_data_failure_bad_extension(file_name):
    path = data_path / file_name
    log_path = pathlib.Path(afmformats.DEFAULT_LOG_PATH)

    with pytest.raises(ValueError,
                       match=r"Unsupported file extension"):
        _ = afmformats.load_data(path)

    with log_path.open(encoding="utf-8") as fd:
        new_output = fd.read()

    assert "afmformats logging initialized" in new_output
    assert "Loader failed" in new_output
