"""Methods to open JPK data files and to obtain meta data"""
import functools
import pathlib

import jprops


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
