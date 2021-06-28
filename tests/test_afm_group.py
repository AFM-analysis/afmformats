"""Test group functionalities"""
import pathlib

import pytest

from afmformats import AFMForceDistance, AFMGroup, load_data


data_dir = pathlib.Path(__file__).parent / "data"


def test_append_bad_type():
    grp = AFMGroup(data_dir / "map2x2_extracted.jpk-force-map")
    with pytest.raises(ValueError, match="must be an instance"):
        grp.append(2)


def test_base():
    grp1 = AFMGroup(data_dir / "map2x2_extracted.jpk-force-map")
    grp2 = load_data(data_dir / "spot3-0192.jpk-force")

    grp3 = grp1 + grp2
    assert len(grp3) == 5
    assert len(grp2) == 1
    assert len(grp1) == 4

    grp2 += grp1
    assert len(grp3) == 5
    assert len(grp2) == 5

    for afmd in grp3:
        assert isinstance(afmd, AFMForceDistance)

    # test repr
    assert "AFMGroup" in repr(grp3)

    # test str
    assert "AFMGroup" in str(grp3)
    assert "spot3-0192.jpk-force" in str(grp3)


def test_enum_index():
    grp = AFMGroup(data_dir / "map2x2_extracted.jpk-force-map")
    afmd = grp.get_enum(2)
    assert afmd.enum == 2
    assert grp.index(afmd) == 2


def test_enum_multiple_error():
    grp = AFMGroup(data_dir / "map2x2_extracted.jpk-force-map")
    grp += load_data(data_dir / "spot3-0192.jpk-force")
    with pytest.raises(ValueError, match="Multiple curves"):
        grp.get_enum(0)


def test_enum_not_found_error():
    grp = AFMGroup(data_dir / "map2x2_extracted.jpk-force-map")
    with pytest.raises(KeyError, match="Could not find"):
        grp.get_enum(100)


def test_iadd_bad_type():
    grp = AFMGroup(data_dir / "map2x2_extracted.jpk-force-map")
    with pytest.raises(ValueError, match="AFMGroup for iadd"):
        grp += 2


def test_meta_override():
    k = 20
    sens = .01e-6
    grp = AFMGroup(
        data_dir / "AFM-workshop_FD_mapping_16_2018-08-01_13.07.zip",
        meta_override={"spring constant": k,
                       "sensitivity": sens})
    assert grp[0].metadata["spring constant"] == k


def test_meta_override_meaningless():
    with pytest.raises(ValueError, match="meaningless"):
        AFMGroup(meta_override={"spring constant": 1,
                                "sensitivity": 2})


def test_subgroup():
    group = AFMGroup()
    group += load_data(data_dir / "map-data-reference-points.jpk-force-map")
    group += load_data(data_dir / "map2x2_extracted.jpk-force-map")
    group += load_data(data_dir / "flipsign_2015.05.22-15.31.49.352.jpk-force")

    exp = data_dir / "map2x2_extracted.jpk-force-map"
    subgrp = group.subgroup_with_path(path=exp)
    assert len(group) == 8
    assert len(subgrp) == 4
    assert subgrp[0].path == exp
