import pathlib

import numpy as np

import pytest

import afmformats

data_dir = pathlib.Path(__file__).resolve().parent / "data"


@pytest.mark.parametrize("name,size,meta", [
    ("spot3-0192.jpk-force", 4000, {}),
    ("AFM-workshop_FD_single_2020-02-14_13.41.25.csv", 2030, {}),
    ("2015_01_17_gel4-0,1_mQ_adh_6B_Curve_DFL_Height_51.txt", 1644,
     {"sensitivity": 61, "spring constant": 0.055}),
    ])
def test_length(name, size, meta):
    jpkfile = data_dir / name
    fdat = afmformats.load_data(jpkfile,
                                modality="force-distance",
                                meta_override=meta,
                                )[0]
    assert len(fdat) == size
    assert np.all(fdat["index"] == np.arange(size))


def test_repr_str():
    jpkfile = data_dir / "spot3-0192.jpk-force"
    fd = afmformats.load_data(jpkfile)[0]
    assert "AFMForceDistance" in str(fd)
    assert "spot3-0192.jpk-force" in str(fd)
    assert "AFMForceDistance" in repr(fd)
    assert "spot3-0192.jpk-force" in repr(fd)
