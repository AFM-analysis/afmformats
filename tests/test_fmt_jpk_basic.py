"""Test of basic opening functionalities"""
import pathlib
import shutil
import tempfile

import numpy as np
import pytest

import afmformats
import afmformats.errors

from afmformats.formats.fmt_jpk.jpk_reader import ArchiveCache


data_path = pathlib.Path(__file__).resolve().parent / "data"


def test_archive_cache():
    td = pathlib.Path(tempfile.mkdtemp(prefix="archive_cache_jpk_"))
    ziplist = []
    for ii in range(ArchiveCache.max_archives + 1):
        pnew = td / f"spot_{ii:03d}.jpk-force"
        shutil.copy2(data_path / "fmt-jpk-fd_spot3-0192.jpk-force", pnew)
        ziplist.append(ArchiveCache.get(pnew))
    assert ziplist[0].fp is None  # we are one over `max_archives`
    assert not ziplist[1].fp is None
    assert not ziplist[-1].fp is None


def test_creep_compliance1():
    jpkfile = data_path / "fmt-jpk-cc_pr14-brain-2021.06.30.jpk-force"
    ds = afmformats.load_data(path=jpkfile)[0]
    assert np.allclose(ds.metadata["duration intermediate"], 3,
                       atol=0, rtol=1e-12)


def test_creep_compliance2():
    jpkfile = data_path / "fmt-jpk-cc_pr14-polymergel-2021.06.30.jpk-force"
    ds = afmformats.load_data(path=jpkfile)[0]
    assert np.allclose(ds.metadata["duration intermediate"], 3,
                       atol=0, rtol=1e-12)


@pytest.mark.parametrize("name, exp_valid",
    [("fmt-jpk-fd_spot3-0192.jpk-force", True),  # noqa: E128
     ("fmt-jpk-fd_map2x2_extracted.jpk-force-map", True),
     # Since 0.18.0 afmformats supports opening calibration files
     ("fmt-jpk-cl_calibration_force-save-2015.02.04-11.25.21.294.jpk-force",
      True),
     ])
def test_detect_jpk(name, exp_valid):
    jpkfile = data_path / name
    recipe = afmformats.formats.get_recipe(path=jpkfile)
    act_valid = recipe.detect(jpkfile)
    assert exp_valid == act_valid

    if not exp_valid:
        with pytest.raises(afmformats.errors.FileFormatNotSupportedError):
            afmformats.load_data(path=jpkfile)


def test_get_z_range():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    ds = afmformats.load_data(path=jpkfile)[0]
    assert np.allclose(ds.metadata["z range"], 4.280850000996709e-06,
                       atol=0, rtol=1e-6)


def test_load_jpk_map():
    jpkfile = data_path / "fmt-jpk-fd_map2x2_extracted.jpk-force-map"
    afmlist = afmformats.load_data(path=jpkfile)

    assert len(afmlist) == 4
    ds = afmlist[2]
    ds2 = afmlist[3]
    assert ds.metadata["enum"] == 2
    assert np.allclose(ds.metadata["duration"], 1.6089775561097257)
    # Verified with visual inspection of force curve in JPK software
    assert np.allclose(ds["force"][0], -5.8540192943834714e-10)
    assert np.allclose(ds["height (measured)"][0], 0.0001001727719556085)
    # make sure curve id is different
    assert ds.metadata["curve id"] != ds2.metadata["curve id"]
    assert ds.metadata["session id"] == ds2.metadata["session id"]


def test_load_jpk_map_modify_metadata():
    jpkfile = data_path / "fmt-jpk-fd_map2x2_extracted.jpk-force-map"

    # initial values
    ds = afmformats.load_data(path=jpkfile)[2]
    init_force = -5.8540192943834714e-10
    assert np.allclose(ds["force"][0], init_force)
    old_spring_constant = ds.metadata["spring constant"]
    new_spring_constant = 10
    assert not np.allclose(old_spring_constant,
                           new_spring_constant), "sanity check"

    # load it again, this time with new metadata
    # (the spring constant is proportional to the force and there is no offset)
    ds2 = afmformats.load_data(path=jpkfile,
                               meta_override={
                                   "spring constant": new_spring_constant})[2]
    new_force = init_force / old_spring_constant * new_spring_constant
    assert np.allclose(ds2["force"][0], new_force)


def test_load_jpk_simple():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    afmlist = afmformats.load_data(path=jpkfile)
    ds = afmlist[0]
    assert ds.metadata["enum"] == 0
    assert np.allclose(ds["height (measured)"][0], 2.2815672438768612e-05)


def test_load_jpk_piezo():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    afmlist = afmformats.load_data(path=jpkfile)
    ds = afmlist[0]
    assert np.allclose(ds["height (piezo)"][0], 2.878322343068329e-05)
