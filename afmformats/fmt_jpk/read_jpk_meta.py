"""Methods to open JPK data files and to obtain meta data"""
import functools
import json
import pathlib
from pkg_resources import resource_filename
import tempfile
import zipfile

import jprops
import numpy as np

from ..errors import FileFormatMetaDataError
from .. import meta


class ReadJPKMetaKeyError(FileFormatMetaDataError):
    pass


def extract_jpk(path_jpk, props_only=False):
    """Extract the JPK data files and return the extracted path"""
    tdir = tempfile.mkdtemp(prefix="afmformats_jpk_")
    with zipfile.ZipFile(str(path_jpk)) as fd:
        if props_only:
            for name in fd.namelist():
                if name.endswith(".properties"):
                    fd.extract(name, tdir)
        else:
            fd.extractall(tdir)
    return pathlib.Path(tdir)


def isnan(obj):
    if isinstance(obj, (str)):
        if obj.lower() == "nan":
            return True
    elif isinstance(obj, float):
        return np.isnan(obj)
    else:
        return False


def get_data_list(path_jpk):
    path_jpk = pathlib.Path(path_jpk)
    with zipfile.ZipFile(str(path_jpk)) as fd:
        files = fd.namelist()
    dfiles = [f for f in files if f.endswith(".dat")]
    # sort files correctly
    segdict = {}
    if "segments/" in files:
        app = [aa for aa in dfiles if aa.startswith("segments/0")]
        ret = [aa for aa in dfiles if aa.startswith("segments/1")]
        segdict["0"] = (app, ret)
    elif "index/" in files:
        segids = [dd.split("/")[1] for dd in dfiles]
        segids = list(set(segids))
        for sid in segids:
            sidstrapp = "index/{}/segments/0".format(sid)
            app = [dd for dd in dfiles if dd.startswith(sidstrapp)]
            sidstrret = "index/{}/segments/1".format(sid)
            ret = [dd for dd in dfiles if dd.startswith(sidstrret)]
            segdict[sid] = (app, ret)
    else:
        msg = "Unknown JPK file format: {}".format(path_jpk)
        raise NotImplementedError(msg)

    segkeys = list(segdict.keys())

    segkeys.sort(key=lambda x: int(x))

    seglist = []
    for key in segkeys:
        seglist.append(segdict[key])
    return seglist


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


def get_meta_data_seg(path_segment):
    """Obtain most important meta-data for a segment folder
    """
    segment = pathlib.Path(path_segment)

    # 1. Populate with primary metadata
    md = meta.MetaData()
    recipe = get_primary_meta_recipe()
    header_file = segment / "segment-header.properties"
    prop = get_seg_head_prop(header_file)

    for key in recipe:
        for vari in recipe[key]:
            if vari in prop:
                md[key] = prop[vari]
                break
    for mkey in ["spring constant",
                 "sensitivity",
                 ]:
        if mkey not in md:
            msg = "Missing meta data: '{}'".format(mkey)
            raise ReadJPKMetaKeyError(msg)

    # Currently, only force-distance mode is supported!
    md["imaging mode"] = "force-distance"
    if segment.name == "0":
        curseg = "approach"
    else:
        curseg = "retract"
    md["software"] = "JPK"

    if ("position x" in md and "position y" in md
        and "grid size x" in md and "grid size y" in md
        and "grid center x" in md and "grid center y" in md
            and "grid shape x" in md and "grid shape y" in md):
        pxpx = position_m2px(pos_m=md["position x"],
                             size_m=md["grid size x"],
                             center_m=md["grid center x"],
                             size_px=md["grid shape x"])
        pypx = position_m2px(pos_m=md["position y"],
                             size_m=md["grid size y"],
                             center_m=md["grid center y"],
                             size_px=md["grid shape y"])
        md["grid index x"] = pxpx
        md["grid index y"] = pypx

    # 2. Populate with secondary metadata
    recipe_2 = get_secondary_meta_recipe()
    md_im = {}

    for key in recipe_2:
        for vari in recipe_2[key]:
            if vari in prop:
                md_im[key] = prop[vari]
                break

    md["curve id"] = "{}:{:g}".format(md["session id"],
                                      md_im["position index"])
    md["setpoint"] = md_im["setpoint [V]"] * \
        md["spring constant"] * md["sensitivity"]

    md["rate " + curseg] = md["point count"] / md["duration"]
    zrange = abs(md_im["z start"] - md_im["z end"])
    md["speed " + curseg] = zrange / md["duration"]
    # date and time
    md["date"], md["time"], _ = md_im["time stamp"].split()

    # Convert designated keys to integers
    integer_keys = ["grid shape x",
                    "grid shape y",
                    "grid index x",
                    "grid index y",
                    "point count",
                    ]
    for ik in integer_keys:
        if ik in md:
            md[ik] = int(round(md[ik]))
    return md


@functools.lru_cache(maxsize=10)
def get_seg_head_prop(path_seg_head_prop):
    """ Obtain the properies of a "segment-header.properties" file

    Parameters
    ----------
    path_seg_head_prop : str
        Full path to a "segment-header.properties" file

    Notes
    -----
    This method also parses these files if present:
    - "shared-data/header.properties"
    - "header.properties"
    """
    path = pathlib.Path(path_seg_head_prop).resolve()
    with path.open(mode="rb") as fd:
        prop = jprops.load_properties(fd)

    # Determine if we have a shared-data file
    # These are positions in the file system that could contain the
    # shared properties files:
    shared_locs = [path.parents[2] / "shared-data",
                   path.parents[4] / "shared-data",
                   ]
    general_locs = [path.parents[2],
                    path.parents[4]
                    ]

    # Loop through the candidates
    for cc in shared_locs:
        shared = cc / "header.properties"
        if shared.exists():
            # A candidate exists. Load its properties.
            psprop = load_prop_file(shared)
            # Generate lists of keys and sort them for easier debugging.
            proplist = list(prop.keys())
            proplist.sort()
            pslist = list(psprop.keys())
            pslist.sort()
            # Loop through the segment data and search for lcd-info tags
            for key in proplist:
                # Get line channel data
                if key.count(".*"):
                    # Replace the lcd-info tag by the values in the shared
                    # properties file:
                    # 0, 1, 2, 3, etc.
                    index = prop[key]
                    # lcd-info, force-segment-header-info
                    mediator = ".".join(key.split(".")[-2:-1])
                    # channel.vDeflection, force-segment-header
                    headkey = key.rsplit(".", 2)[0]
                    # append a "." here to make sure
                    # not to confuse "1" with "10".
                    startid = "{}.{}.".format(mediator, index)

                    for k2 in pslist:
                        if k2.startswith(startid):
                            var = ".".join(k2.split(".")[2:])
                            prop[".".join([headkey, var])] = psprop[k2]

    for gg in general_locs:
        gen = gg / "header.properties"
        if gen.exists():
            gsprop = load_prop_file(gen)
            # Add all other keys
            for pk in gsprop:
                prop[pk] = gsprop[pk]

    for p in prop:
        try:
            prop[p] = float(prop[p])
        except BaseException:
            pass

    return prop


@functools.lru_cache(maxsize=10)
def load_prop_file(path):
    path = pathlib.Path(path)
    with path.open(mode="rb") as fd:
        props = jprops.load_properties(fd)
    return props


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
