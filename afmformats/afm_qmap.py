import functools

import numpy as np

from .afm_group import AFMGroup
from .meta import META_FIELDS


__all__ = ["AFMQMap", "qmap_feature", "unit_scales"]


def qmap_feature(name, unit, cache=False):
    """Decorator for labeling AFMQMap features

    The name and unit are stored as properties of the wrapped function.
    In addition, the return value of the function can be cached (see
    `cache` argument).

    Parameters
    ----------
    name: str
        Name of the feature
    unit: str
        Unit of the returned feature
    cache: bool or callable
        If boolean, determines whether the feature data should be
        cached or not. If callable, the callable gets an instance
        of AFMData as an argument and should return an identifier
        (str) for the current value. If that identifier is the
        same as in the cache, then the cached value is used.
    """
    def attribute_setter(func):
        """Decorator that sets the necessary attributes

        The outer decorator is used to obtain the attributes.
        This inner decorator returns the actual function that
        wraps the feature function.
        """
        func.name = name
        func.unit = unit
        if isinstance(cache, bool):
            if cache:
                # cache everything once
                func.cache_mode = "static"
                func.cache_values = {}
            else:
                # disable caching
                func.cache_mode = "disabled"
        else:
            assert isinstance(cache, callable)
            func.cache_mode = "variable"
            func.cache_values = {}
            func.cache_ids = {}
            func.cache_getid = cache

        @functools.wraps(func)
        def cached_func(afmdata):
            afmdataid = hex(id(afmdata))
            if func.cache_mode == "disabled":
                # no caching
                return func(afmdata)
            elif func.cache_mode == "static":
                # caching is done only once
                if afmdataid not in func.cache_values:
                    func.cache_values[afmdataid] = func(afmdata)
                return func.cache_values[afmdataid]
            else:
                # we have to check whether we have to recompute
                cid = func.cache_getid(afmdata)
                assert cid, "Must not be empty string"
                if func.cache_ids.get(afmdataid, "") != cid:
                    # recompute the value
                    func.cache_values[afmdataid] = func(afmdata)
                    func.cache_ids[afmdataid] = cid
                return func.cache_values[afmdataid]

        return cached_func

    return attribute_setter


class AFMQMap:
    """Management of quantitative AFM data on a grid"""
    def __init__(self, path_or_group, meta_override=None, callback=None,
                 data_classes_by_modality=None):
        """
        Parameters
        ----------
        path_or_group: str or pathlib.Path or afmformats.afm_group.AFMGroup
            The path to the data file or an instance of `AFMGroup`
        meta_override: dict
            Dictionary with metadata that is used when loading the data
            in `path`.
        callback: callable or None
            A method that accepts a float between 0 and 1
            to externally track the process of loading the data.
        data_classes_by_modality: dict
            Override the default AFMData class to use for managing the data
            (see :data:`default_data_classes_by_modality`): This is e.g.
            used by :ref:`nanite:index` to pass `Indentation` (which is a
            subclass of the default `AFMForceDistance`) for handling
            "force-indentation" data.
        """
        if isinstance(path_or_group, AFMGroup):
            group = path_or_group
            if meta_override is not None:
                raise ValueError(
                    "Specifying `meta_override` for an AFMGroup instance "
                    "that is already populated is meaningless.")
        else:
            group = AFMGroup(path=path_or_group,
                             meta_override=meta_override,
                             callback=callback,
                             data_classes_by_modality=data_classes_by_modality)
        #: AFM data (instance of :class:`afmformats.afm_group.AFMGroup`)
        self.group = group

        # sanity check (make sure that all necessary metadata are available)
        missing_keys = []
        for key in META_FIELDS["qmap"]:
            if key not in self.group[0].metadata:
                missing_keys.append(key)
        if missing_keys:
            raise ValueError(f"QMap metadata missing for '{self.group.path}': "
                             + ", ".join(missing_keys))

        # Register feature functions
        #: Available features
        self.features = []
        self._feature_funcs = {}
        self._feature_units = {}
        fnames = [f for f in dir(self) if f.startswith("feat_")]
        for fn in fnames:
            func = getattr(self, fn)
            assert func.name not in self._feature_funcs
            assert func.name not in self._feature_units
            self._feature_funcs[func.name] = func
            self._feature_units[func.name] = func.unit
            self.features.append(func.name)

    def _map_grid(self, coords, map_data):
        """Create a 2D map from 1D coordinates and data

        The .jpk-force-map file format stores the map data in a
        seemingly arbitrary way. This method converts a set of
        coordinates and map data values to a 2D map.

        Parameters
        ----------
        coords: list-like (length N) with tuple of ints
            The x- and y-coordinates [px].
        map_data: list-like (length N)
            The data to be mapped.

        Returns
        -------
        x, y: 1d ndarrays
            The x- and y-values that label the axes of the map
        map2d: 2d ndarray
            The ordered map data.
        """
        shape = self.shape
        extent = self.extent

        coords = np.array(coords)
        map_data = np.array(map_data)

        xn, yn = int(shape[0]), int(shape[1])

        # Axes ticks
        x, dx = np.linspace(extent[0], extent[1], xn,
                            endpoint=False, retstep=True)
        y, dy = np.linspace(extent[2], extent[3], yn,
                            endpoint=False, retstep=True)
        x += dx/2
        y += dy/2

        # Output map
        map2d = np.zeros((yn, xn), dtype=float)*np.nan
        for ii in range(map_data.shape[0]):
            # Determine the coordinate in the output array
            xi, yi = coords[ii]
            # Write to the output array
            map2d[yi, xi] = map_data[ii]

        return x, y, map2d

    @property
    @functools.lru_cache(maxsize=32)
    def extent(self):
        """extent (x1, x2, y1, y2) [µm]"""
        afmdata0 = self.group[0]
        # get extent of the map
        sx = afmdata0.metadata["grid size x"] * 1e6
        sy = afmdata0.metadata["grid size y"] * 1e6
        cx = afmdata0.metadata["grid center x"] * 1e6
        cy = afmdata0.metadata["grid center y"] * 1e6
        extent = (cx - sx/2, cx + sx/2,
                  cy - sy/2, cy + sy/2,
                  )
        return extent

    @property
    @functools.lru_cache(maxsize=32)
    def shape(self):
        """shape of the map [px]"""
        afmdata0 = self.group[0]
        # get shape of the map
        shape = (afmdata0.metadata["grid shape x"],
                 afmdata0.metadata["grid shape y"]
                 )
        return shape

    @staticmethod
    @qmap_feature(name="data: height base point",
                  unit="µm",
                  cache=True)
    def feat_core_data_height_base_point_um(afmdata):
        """Compute the lowest height (measured)"""
        height = np.min(afmdata["height (measured)"])
        value = height / unit_scales["µ"]
        return value

    @staticmethod
    @qmap_feature(name="data: piezo range",
                  unit="µm",
                  cache=True)
    def feat_core_data_piezo_range_um(afmdata):
        """Compute peak-to-peak piezo range"""
        return afmdata.metadata["z range"] / unit_scales["µ"]

    @staticmethod
    @qmap_feature(name="data: scan order",
                  unit="",
                  cache=True)
    def feat_core_data_scan_order(afmdata):
        """Return the enumeration of the dataset"""
        return afmdata.enum

    @functools.lru_cache(maxsize=32)
    def get_coords(self, which="px"):
        """Get the qmap coordinates for each curve in `AFMQMap.group`

        Parameters
        ----------
        which: str
            "px" for pixels or "um" for microns.
        """
        if which not in ["px", "um"]:
            raise ValueError("`which` must be 'px' or 'um'!")

        if which == "px":
            kx = "grid index x"
            ky = "grid index y"
            mult = 1
        else:
            kx = "position x"
            ky = "position y"
            mult = 1e6
        coords = []
        for afmdata in self.group:
            # We assume that kx and ky are given. This has to be
            # ensured by the file format reader for qmaps.
            cc = [afmdata.metadata[kx] * mult, afmdata.metadata[ky] * mult]
            coords.append(cc)
        return np.array(coords)

    def get_qmap(self, feature, qmap_only=False):
        """Return the quantitative map for a feature

        Parameters
        ----------
        feature: str
            Feature to compute map for (see :data:`QMap.features`)
        qmap_only:
            Only return the quantitative map data,
            not the coordinates

        Returns
        -------
        x, y: 1d ndarray
            Only returned if `qmap_only` is False; Pixel grid
            coordinates along x and y
        qmap: 2d ndarray
            Quantitative map
        """
        coords = self.get_coords(which="px")

        map_data = []
        ffunc = self._feature_funcs[feature]
        for afmdata in self.group:
            val = ffunc(afmdata)
            map_data.append(val)

        x, y, qmap = self._map_grid(coords=coords, map_data=map_data)
        if qmap_only:
            return qmap
        else:
            return x, y, qmap


unit_scales = {"": 1,
               "k": 1e3,
               "m": 1e-3,
               "µ": 1e-6,
               "n": 1e-9,
               "p": 1e-12
               }
