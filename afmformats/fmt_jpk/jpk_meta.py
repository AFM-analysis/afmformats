import functools
import json
from pkg_resources import resource_filename

import numpy as np

from ..errors import FileFormatMetaDataError


__all__ = ["ReadJPKMetaKeyError",
           "get_primary_meta_recipe",
           "get_secondary_meta_recipe",
           "position_m2px",
           ]


class ReadJPKMetaKeyError(FileFormatMetaDataError):
    pass


@functools.lru_cache()
def get_primary_meta_recipe():
    with open(resource_filename("afmformats.fmt_jpk",
                                "jpk_meta_primary.json")) as fd:
        meta_recipe_pri = json.load(fd)
    return meta_recipe_pri


@functools.lru_cache()
def get_secondary_meta_recipe():
    with open(resource_filename("afmformats.fmt_jpk",
                                "jpk_meta_secondary.json")) as fd:
        meta_recipe_sec = json.load(fd)
    return meta_recipe_sec


def position_m2px(pos_m, size_m, center_m, size_px):
    """Convert qmap positions from [m] to array coordinates in [px]

    Parameters
    ----------
    pos_m: float
        positions [m]
    size_m: float
        grid size [m]
    center_m: float
        grid center position [m]
    size_px: int
        grid size [px]

    Returns
    -------
    pos_px: int
        index position of `pos_m`
    """
    if size_px != int(size_px):
        raise ValueError("`size_px` must be integer, got {}!".format(size_px))
    size_px = int(size_px)
    s1 = center_m - size_m / 2
    s2 = center_m + size_m / 2

    x, dx = np.linspace(s1, s2, size_px, endpoint=False, retstep=True)
    x += dx / 2

    xpx = np.nanargmin(np.abs(x - pos_m))
    return xpx
