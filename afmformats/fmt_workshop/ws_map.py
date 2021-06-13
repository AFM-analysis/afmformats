import io
import pathlib
import warnings
import zipfile

from .ws_single import AFMWorkshopFormatWarning, load_csv


__all__ = ["load_map"]


def load_map(path, callback=None, meta_override=None):
    """Load a set of zipped csv AFM workshop data

    If you are recording quantitative force-maps (i.e. multiple
    curves on an x-y-grid) with AFM workshop setups, then you
    might have realized that you get *multiple* .csv files (one
    file per indentation) instead of *one* file that contains all
    the data (as you might be accustomed to from other
    manufacturers). Since afmformats expects one file per
    measurement, it would not be straight forward to obtain a
    properly enumerated quantitative imaging group.

    This function offers a workaround - it loads a zip archive
    created from the the .csv files.

    The files are structured like this::

        Force-Distance Curve
        File Format:    3

        Date:    Wednesday, August 1, 2018
        Time:    1:07:47 PM
        Mode:    Mapping
        Point:    16
        X, um:    27.250000
        Y, um:    27.250000

        Extend Z-Sense(nm),Extend T-B(V),Retract Z-Sense(nm),Retract T-B(V)
        13777.9288,0.6875,14167.9288,1.0917
        13778.9288,0.6874,14166.9288,1.0722
        13779.9288,0.6876,14165.9288,1.0693
        13780.9288,0.6877,14164.9288,1.0824
        13781.9288,0.6875,14163.9288,1.0989
        ...

    Please make sure that the ``Point`` is enumerated from 1
    onwards (and matches the alphanumerical order of the files in
    the archive) and that ``Mode`` is ``Mapping``. The ``X`` and
    ``Y`` coordinates can be used by e.g. PyJibe to display QMap
    data on a grid.
    """
    datasets = []
    with zipfile.ZipFile(path) as arc:
        for ii, name in enumerate(sorted(arc.namelist())):
            with arc.open(name, "r") as fd:
                tfd = io.TextIOWrapper(fd, encoding="utf-8")
                dd = load_csv(tfd, meta_override=meta_override, mode="mapping")
                dd[0]["metadata"]["path"] = pathlib.Path(path)
                cur_enum = dd[0]["metadata"]["enum"]
                if cur_enum != ii + 1:
                    warnings.warn("Dataset 'Point' enumeration mismatch for "
                                  f"'{name}' in '{path}' (expected {ii+1}, "
                                  f"got {cur_enum})!",
                                  AFMWorkshopFormatWarning)
                datasets += dd
    return datasets
