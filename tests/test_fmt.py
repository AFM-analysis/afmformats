import pathlib

import pytest

import afmformats
import afmformats.formats
import afmformats.errors


data_path = pathlib.Path(__file__).parent / "data"


@pytest.mark.parametrize("path", data_path.glob("fmt-*-fd_*"))
def test_load_force_distance_modality(path):
    recipe = afmformats.formats.get_recipe(path)
    assert recipe.get_modality(path) == "force-distance"


@pytest.mark.parametrize("path", data_path.glob("fmt-*-fd_*"))
def test_load_force_distance_with_callback(path):
    """Make sure that the callback function is properly implemented"""
    calls = []

    def callback(value):
        calls.append(value)

    try:
        afmformats.load_data(path=path, callback=callback)
    except afmformats.errors.MissingMetaDataError:
        afmformats.load_data(path=path,
                             callback=callback,
                             meta_override={"spring constant": 20,
                                            "sensitivity": .01e-6})
    assert calls[-1] == 1


@pytest.mark.parametrize("path", data_path.glob("fmt-*-cc_*"))
def test_load_creep_compliance_modality(path):
    recipe = afmformats.formats.get_recipe(path)
    assert recipe.get_modality(path) == "creep-compliance"


@pytest.mark.parametrize("path", data_path.glob("fmt-*-cc_*"))
def test_load_creep_compliance_with_callback(path):
    """Make sure that the callback function is properly implemented"""
    calls = []

    def callback(value):
        calls.append(value)

    try:
        afmd = afmformats.load_data(path=path, callback=callback)
    except afmformats.errors.MissingMetaDataError:
        afmd = afmformats.load_data(path=path,
                                    callback=callback,
                                    meta_override={"spring constant": 20,
                                                   "sensitivity": .01e-6})
    for cc in afmd:
        assert cc.modality == "creep-compliance"
    assert calls[-1] == 1
