import pathlib

import numpy as np

import pytest

import afmformats

data_path = pathlib.Path(__file__).resolve().parent / "data"


@pytest.mark.parametrize("name,size,meta", [
    ("fmt-jpk-fd_spot3-0192.jpk-force", 4000, {}),
    ("fmt-afm-workshop-fd_single_2020-02-14_13.41.25.csv", 2030, {}),
    ("fmt-ntmdt-txt-fd_2015_01_17_gel4-0,1_mQ_adh_6B_Curve_DFL_Height_51.txt",
     1644,
     {"sensitivity": 61, "spring constant": 0.055}),
])
def test_length(name, size, meta):
    jpkfile = data_path / name
    fdat = afmformats.load_data(jpkfile,
                                modality="force-distance",
                                meta_override=meta,
                                )[0]
    assert len(fdat) == size
    assert np.all(fdat["index"] == np.arange(size))


def test_repr_str():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    fd = afmformats.load_data(jpkfile)[0]
    assert "AFMForceDistance" in str(fd)
    assert "fmt-jpk-fd_spot3-0192.jpk-force" in str(fd)
    assert "AFMForceDistance" in repr(fd)
    assert "fmt-jpk-fd_spot3-0192.jpk-force" in repr(fd)


def test_reset():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    fd = afmformats.load_data(jpkfile)[0]
    fd["tip position"] = np.linspace(0, 1, len(fd))
    assert "tip position" in fd
    assert "tip position" not in fd.columns_innate
    fd.reset_data()
    assert "tip position" not in fd


def test_segment():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    fd = afmformats.load_data(jpkfile)[0]
    assert np.sum(fd["segment"] == 0) == 2000
    assert fd.appr["segment"].size == 2000

    new_segment = np.zeros_like(fd["segment"])
    new_segment[500:] = 1
    fd["segment"] = new_segment
    assert np.sum(fd["segment"] == 0) == 500
    assert fd.appr["segment"].size == 500

    new_segment2 = np.zeros_like(fd["segment"])
    new_segment2[600:] = 1
    fd["segment"] = new_segment2
    assert np.sum(fd["segment"] == 0) == 600
    assert fd.appr["segment"].size == 600


def test_segment_set_item():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    fd = afmformats.load_data(jpkfile)[0]

    fd["tip position"] = np.ones(len(fd))
    assert np.all(fd.appr["tip position"] == np.ones(2000))
    fd.appr["tip position"] = 2*np.ones(2000)
    assert np.all(fd.appr["tip position"] == 2*np.ones(2000))
    assert np.all(fd.retr["tip position"] == np.ones(2000))
    assert np.all(fd["tip position"] == np.concatenate([2*np.ones(2000),
                                                        np.ones(2000)]))


def test_segment_set_item_2():
    jpkfile = data_path / "fmt-jpk-fd_spot3-0192.jpk-force"
    fd = afmformats.load_data(jpkfile)[0]

    data = fd["height (measured)"]
    fd.appr["height (measured)"] = np.arange(2000)

    # test override not taking place
    assert not np.all(data[:2000] == np.arange(2000))
    # data access tests
    assert np.all(data[2000:] == fd["height (measured)"][2000:])
    assert np.all(fd["height (measured)"][2000:]
                  == fd.retr["height (measured)"])
    # test with private property
    assert np.all(fd.appr["height (measured)"]
                  == fd.appr._data["height (measured)"][:2000])
    assert not np.all(fd.appr["height (measured)"]
                      == fd.appr._raw_data["height (measured)"][:2000])
