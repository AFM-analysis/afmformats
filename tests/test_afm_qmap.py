import pathlib
from unittest import mock

import pytest

import numpy as np

from afmformats import AFMGroup, AFMQMap

data_dir = pathlib.Path(__file__).parent / "data"


def test_feat_scan_order():
    qm = AFMQMap(data_dir / "map2x2_extracted.jpk-force-map")
    order = qm.get_qmap("meta: scan order", qmap_only=True)
    assert order[0, 0] == 0
    assert order[0, -1] == 1
    assert order[-1, -1] == 2
    assert order[-1, 0] == 3
    assert np.isnan(order[0, 1])


def test_feat_min_height():
    qm = AFMQMap(data_dir / "map2x2_extracted.jpk-force-map")
    qd = qm.get_qmap("data: lowest height", qmap_only=True)
    assert np.allclose(qd[0, 0], 40.55030392499141)
    assert np.allclose(qd[0, -1], 47.354988549298945)
    assert np.allclose(qd[-1, -1], 96.1627883099352)
    assert np.allclose(qd[-1, 0], 89.95170867840217)


def test_get_coords():
    qm = AFMQMap(data_dir / "map2x2_extracted.jpk-force-map")

    px = qm.get_coords(which="px")
    refpx = np.array([[0, 0], [9, 0], [9, 9], [0, 9]])
    assert np.all(px == refpx)

    um = qm.get_coords(which="um")
    refum = np.array([[31.972656250000004, -753.5351562500001],
                      [571.8359375000001, -753.90625],
                      [571.8359375000001, -213.73046875000003],
                      [31.855468750000004, -213.73046875000003]])
    assert np.all(um == refum)


def test_get_coords_bad():
    qm = AFMQMap(data_dir / "map2x2_extracted.jpk-force-map")
    try:
        qm.get_coords(which="mm")
    except ValueError:
        pass
    else:
        assert False, "Units [mm] should not be supported."


def test_get_qmap():
    qm = AFMQMap(data_dir / "map2x2_extracted.jpk-force-map")
    x, y, _ = qm.get_qmap(feature="data: lowest height", qmap_only=False)
    assert x.size == 10
    assert y.size == 10


def test_init_with_group():
    group = AFMGroup(data_dir / "map2x2_extracted.jpk-force-map")
    qm = AFMQMap(group)
    assert qm.shape == (10, 10)


def test_init_with_group_meta_override_meaningless():
    group = AFMGroup(data_dir / "map2x2_extracted.jpk-force-map")
    with pytest.raises(ValueError, match="meaningless"):
        AFMQMap(group,
                meta_override={"spring constant": 1,
                               "sensitivity": 2})


def test_metadata_missing():
    fake_qmap_dict = {
        "test-key": ["A description for the test key", "m", float],
        }
    group = AFMGroup(data_dir / "map2x2_extracted.jpk-force-map")
    with mock.patch("afmformats.afm_qmap.META_FIELDS",
                    {"qmap": fake_qmap_dict}):
        with pytest.raises(ValueError,
                           match="QMap metadata missing .* test-key"):
            AFMQMap(group)


def test_shape():
    qm = AFMQMap(data_dir / "map2x2_extracted.jpk-force-map")
    assert np.allclose(qm.extent,
                       [1.97265625, 601.97265625,
                        -783.53515625, -183.53515625000006])
    assert qm.shape == (10, 10)
