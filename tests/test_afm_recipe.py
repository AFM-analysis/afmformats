"""Test AFMFormatRecipe"""
import pathlib
import shutil
import tempfile

import pytest

import afmformats


data_path = pathlib.Path(__file__).resolve().parent / "data"


def test_bad_recipe_loader_missing():
    recipe = {
        "descr": "unknown description",
        "maker": "unknown maker",
        "modality": "force-distance",
        "suffix": ".unknown",
    }
    with pytest.raises(ValueError):
        afmformats.formats.register_format(recipe)


def test_bad_recipe_loader_not_callable():
    recipe = {
        "descr": "unknown description",
        "loader": "peter",
        "maker": "unknown maker",
        "modality": "force-distance",
        "suffix": ".unknown",
    }
    with pytest.raises(ValueError):
        afmformats.formats.register_format(recipe)


def test_bad_recipe_modality_invlaid():
    recipe = {
        "descr": "unknown description",
        "loader": lambda x: x,
        "maker": "unknown maker",
        "suffix": ".unknown",
        "modality": "invalid",
    }
    with pytest.raises(ValueError):
        afmformats.formats.register_format(recipe)


def test_bad_recipe_modality_missing():
    recipe = {
        "descr": "unknown description",
        "loader": lambda x: x,
        "maker": "unknown maker",
        "suffix": ".unknown",
    }
    with pytest.raises(ValueError):
        afmformats.formats.register_format(recipe)


def test_bad_recipe_suffix_invalid():
    recipe = {
        "descr": "unknown description",
        "loader": lambda x: x,
        "maker": "unknown maker",
        "modality": "force-distance",
    }
    with pytest.raises(ValueError):
        afmformats.formats.register_format(recipe)


@pytest.mark.parametrize("name, is_valid",
    [("fmt-jpk-fd_spot3-0192.jpk-force", True),  # noqa: E128
     ("fmt-jpk-fd_map2x2_extracted.jpk-force-map", True),
     # Since version 0.18.0, afmformats supports opening calibration curves
     ("fmt-jpk-cl_calibration_force-save-2015.02.04-11.25.21.294.jpk-force",
      True),
     ])
def test_find_data(name, is_valid):
    file = data_path / name
    file_list = afmformats.find_data(file)
    assert bool(len(file_list)) == is_valid


def test_find_data_recursively():
    td = pathlib.Path(tempfile.mkdtemp(prefix="find_data_recursively_"))
    td2 = td / "test" / "recur"
    td2.mkdir(exist_ok=True, parents=True)
    td3 = td / "test" / "recur2"
    td3.mkdir(exist_ok=True, parents=True)
    shutil.copy2(data_path / "fmt-jpk-fd_spot3-0192.jpk-force", td2)
    shutil.copy2(
        data_path /
        "fmt-jpk-cl_calibration_force-save-2015.02.04-11.25.21.294.jpk-force",
        td3)
    file_list = afmformats.find_data(td)
    # Since version 0.18.0, afmformats supports opening calibration curves
    assert len(file_list) == 2
    assert file_list[0].samefile(td2 / "fmt-jpk-fd_spot3-0192.jpk-force")


def test_find_data_invalid_missing():
    td = pathlib.Path(tempfile.mkdtemp(prefix="find_data_invalid_"))
    shutil.copy2(data_path / "fmt-jpk-fd_spot3-0192.jpk-force",
                 td / "spot.unknown")
    file_list = afmformats.find_data(td)
    assert not file_list
