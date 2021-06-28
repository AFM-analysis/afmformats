import functools

import numpy as np

from .afm_group import AFMGroup
from .meta import META_FIELDS


class DataMissingWarning(UserWarning):
    pass


class AFMQMap(object):
    """Management of quantitative AFM data on a grid"""
    def __init__(self, path_or_group, meta_override=None, callback=None):
        """Quantitative force spectroscopy map handling

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
                             callback=callback)
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
            name, unit = func.__doc__.split("\n")[0].split("[", 1)
            name = name.strip()
            unit = unit.strip().strip("]")
            assert name not in self._feature_funcs
            assert name not in self._feature_units
            self._feature_funcs[name] = func
            self._feature_units[name] = unit
            self.features.append(name)

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
        idnt0 = self.group[0]
        # get extent of the map
        sx = idnt0.metadata["grid size x"] * 1e6
        sy = idnt0.metadata["grid size y"] * 1e6
        cx = idnt0.metadata["grid center x"] * 1e6
        cy = idnt0.metadata["grid center y"] * 1e6
        extent = (cx - sx/2, cx + sx/2,
                  cy - sy/2, cy + sy/2,
                  )
        return extent

    @property
    @functools.lru_cache(maxsize=32)
    def shape(self):
        """shape of the map [px]"""
        idnt0 = self.group[0]
        # get shape of the map
        shape = (idnt0.metadata["grid shape x"],
                 idnt0.metadata["grid shape y"]
                 )
        return shape

    @staticmethod
    def feat_core_data_min_height_measured_um(idnt):
        """data: lowest height [µm]"""
        height = np.min(idnt["height (measured)"])
        value = height / unit_scales["µ"]
        return value

    @staticmethod
    def feat_core_meta_scan_order(idnt):
        """meta: scan order []"""
        return idnt.enum

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
        for idnt in self.group:
            # We assume that kx and ky are given. This has to be
            # ensured by the file format reader for qmaps.
            cc = [idnt.metadata[kx] * mult, idnt.metadata[ky] * mult]
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
        for idnt in self.group:
            val = ffunc(idnt)
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
