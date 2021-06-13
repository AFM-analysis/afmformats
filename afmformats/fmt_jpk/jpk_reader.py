import copy
import functools
import zipfile

import jprops
import numpy as np

from .. import meta

from . import jpk_data, jpk_meta


__all__ = ["JPKReader"]


class JPKReader(object):
    def __init__(self, path):
        self.path = path

    @functools.lru_cache()
    def __len__(self):
        return len(self.get_index_numbers())

    @property
    @functools.lru_cache()
    def files(self):
        """List of files and folders in the archive"""
        with self.get_archive() as arc:
            nlist = arc.namelist()
        maxdigits = int(np.ceil(np.log10(len(nlist)))) + 1
        repstr = "{:0" + "{}".format(maxdigits) + "d}"

        def sortkey(x):
            if x.count("/"):
                xs = x.split("/")
                for ii in range(len(xs)):
                    if xs[ii].isnumeric():
                        xs[ii] = repstr.format(int(xs[ii]))
                return "/".join(xs)
            else:
                return x

        return sorted(nlist, key=sortkey)

    @property
    @functools.lru_cache()
    def hierarchy(self):
        """Format hierarchy ("single" or "indexed")"""
        if "segments/" in self.files:
            return "single"
        elif "index/" in self.files:
            return "indexed"
        else:
            msg = "Cannot determine hierarchy: {}".format(self.path)
            raise NotImplementedError(msg)

    @property
    @functools.lru_cache()
    def _properties_general(self):
        """Return content of "header.properties"""
        with self.get_archive() as arc:
            with arc.open("header.properties", "r") as fd:
                props = jprops.load_properties(fd)
        return props

    @property
    @functools.lru_cache()
    def _properties_shared(self):
        """Return content of "shared-data/header.properties"""
        path = "shared-data/header.properties"
        if path in self.files:
            with self.get_archive() as arc:
                with arc.open(path, "r") as fd:
                    props = jprops.load_properties(fd)
        else:
            props = {}
        return props

    @functools.lru_cache()
    def _get_index_segment_properties(self, index, segment):
        """Return properties fro a specific index and segment

        Parameters
        ----------
        index: int
            Curve index; For "single" hierarchy files, this should be 0.
        segment: int or None
            If None, then no segment-specific properties (e.g.
            approach or retract) are returned.
        """
        # 1. Properties of index
        p_index = self.get_index_path(index) + "header.properties"
        with self.get_archive() as arc:
            with arc.open(p_index, "r") as fd:
                prop = jprops.load_properties(fd)

        # 2. Properties of segment (if applicable)
        if segment is not None:
            p_segment = self.get_index_segment_path(index, segment) \
                        + "segment-header.properties"
            with self.get_archive() as arc:
                with arc.open(p_segment, "r") as fd:
                    prop.update(jprops.load_properties(fd))

        # 3. Substitute shared properties
        psprop = self._properties_shared
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
                pindex = prop[key]
                # lcd-info, force-segment-header-info
                mediator = ".".join(key.split(".")[-2:-1])
                # channel.vDeflection, force-segment-header
                headkey = key.rsplit(".", 2)[0]
                # append a "." here to make sure
                # not to confuse "1" with "10".
                startid = "{}.{}.".format(mediator, pindex)
                for k2 in pslist:
                    if k2.startswith(startid):
                        var = ".".join(k2.split(".")[2:])
                        prop[".".join([headkey, var])] = psprop[k2]

        # 4. Update with general properties
        # (for "single" hierarchy, this coincides with index properties)
        prop.update(self._properties_general)

        # 5. Try to convert numbers to floats
        for p in prop:
            try:
                prop[p] = float(prop[p])
            except BaseException:
                pass
        return prop

    def get_archive(self):
        return zipfile.ZipFile(self.path, mode="r")

    def get_data(self, column, index, segment=None):
        """Return data for a given column, index, or segment

        Parameters
        ----------
        column: str
            Valid column from :const:`afmformats.afm_data.known_columns`
        index: int
            Curve index in the current archive
        segment: int or None
            Segment index for chosen curve index

        Returns
        -------
        data: 1d ndarray
            Column data
        """
        numsegs = self.get_index_segment_numbers(index)
        if segment is None:
            # Return concatenated data for all segments
            data = []
            for seg in numsegs:
                data.append(self.get_data(column=column, index=index,
                                          segment=seg))
            return np.concatenate(data)
        md = self.get_metadata(index, segment)
        prop = self._get_index_segment_properties(index, segment)
        numsegs = self.get_index_segment_numbers(index)
        # Find the data file that corresponds to the specified column
        if column == "time":
            # get initial time
            start = 0
            if segment != 0:
                for seg in numsegs:
                    if seg < segment:
                        start += self.get_metadata(index, seg)["duration"]

            return np.linspace(start, start + md["duration"],
                               md["point count"], endpoint=False)
        elif column == "segment":
            if len(numsegs) <= 2:
                dtype = bool
            else:
                dtype = np.uint8
            return np.ones(md["point count"], dtype=dtype) * dtype(segment)
        else:
            # get the segment's data list
            p_seg = self.get_index_segment_path(index, segment)
            loc_list = [ff for ff in self.files if ff.count(p_seg)]
            name, slot, dat = jpk_data.find_column_dat(loc_list, column)
            with self.get_archive() as arc:
                with arc.open(dat, "r") as fd:
                    data, unit, _ = jpk_data.load_dat_unit(fd, name=name,
                                                           properties=prop,
                                                           slot=slot)
            # verify unit
            if unit != jpk_data.JPK_UNITS[column]:
                raise jpk_data.ReadJPKError("Unknown unit for {}: {}".format(
                    column, unit))
            return data

    @functools.lru_cache()
    def get_index_numbers(self):
        """Return int array with available index numbers

        The numbers is what we refer to as "enum" in afmformats.
        Sometimes individual curves are missing from JPK files.
        These have to be correctly indexed.
        """
        indices = []
        if self.hierarchy == "single":
            indices.append(0)
        else:
            # TODO: is there a more efficient way?
            for ff in self.files:
                if (ff.startswith("index/")
                        and ff.count("/") == 2
                        and ff.endswith("/")):
                    indices.append(int(ff.split("/")[1]))
        indices = np.array(indices, dtype=int)
        return indices

    @functools.lru_cache()
    def get_index_path(self, index):
        """Return the path in the zip file for a specific curve index"""
        enum = self.get_index_numbers()[index]
        if self.hierarchy == "single":
            path = ""
        elif self.hierarchy == "indexed":
            path = "index/{}/".format(enum)
        else:
            raise NotImplementedError("No rule to get path for hierarchy "
                                      + "'{}'!".format(self.hierarchy))
        if path and path not in self.files:
            raise IndexError("Cannot find path for index '{}' ".format(index)
                             + " (enum '{}')!".format(enum))
        return path

    @functools.lru_cache()
    def get_index_segment_numbers(self, index):
        """Return available segment numbers for an index"""
        segments = []
        seg = 0
        while True:
            try:
                self.get_index_segment_path(index, seg)
            except IndexError:
                break
            else:
                segments.append(seg)
                seg += 1
        return segments

    @functools.lru_cache()
    def get_index_segment_path(self, index, segment):
        """Return the path in the zip file for a specific index and segment"""
        enum = self.get_index_numbers()[index]
        if self.hierarchy == "single":
            path = "segments/{}/".format(segment)
        elif self.hierarchy == "indexed":
            path = "index/{}/segments/{}/".format(enum, segment)
        else:
            raise NotImplementedError("No rule to get path for hierarchy "
                                      + "'{}'!".format(self.hierarchy))
        if path not in self.files:
            raise IndexError("Cannot find path for index '{}' ".format(index)
                             + "(enum '{}')".format(enum))
        return path

    @functools.lru_cache()
    def get_metadata(self, index, segment=None):
        """Return the metadata for a specific index and segment

        Parameters
        ----------
        index: int
            Curve index; For "single" hierarchy files, this should be 0.
        segment: int or None
            If None, then all segment-specific properties (e.g.
            approach and retract) are returned.
        """
        if segment is None:
            md = meta.MetaData()
            # reverse order, because we want "time" from first md
            for seg in self.get_index_segment_numbers(index)[::-1]:
                mdap = copy.deepcopy(self.get_metadata(index, seg))
                if "duration" in md:
                    md["duration"] += mdap.pop("duration")
                if "point count" in md:
                    md["point count"] += mdap.pop("point count")
                md.update(mdap)
            return md
        prop = self._get_index_segment_properties(index=index, segment=segment)
        # 1. Populate with primary metadata
        md = meta.MetaData()
        recipe = jpk_meta.get_primary_meta_recipe()
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
                raise jpk_meta.ReadJPKMetaKeyError(msg)

        # Currently, only force-distance mode is supported!
        md["imaging mode"] = "force-distance"
        if int(segment) == 0:
            curseg = "approach"
        else:
            curseg = "retract"
        md["software"] = "JPK"

        md["enum"] = int(self.get_index_numbers()[index])
        md["path"] = self.path

        if ("position x" in md and "position y" in md
                and "grid size x" in md and "grid size y" in md
                and "grid center x" in md and "grid center y" in md
                and "grid shape x" in md and "grid shape y" in md):
            pxpx = jpk_meta.position_m2px(pos_m=md["position x"],
                                          size_m=md["grid size x"],
                                          center_m=md["grid center x"],
                                          size_px=md["grid shape x"])
            pypx = jpk_meta.position_m2px(pos_m=md["position y"],
                                          size_m=md["grid size y"],
                                          center_m=md["grid center y"],
                                          size_px=md["grid shape y"])
            md["grid index x"] = pxpx
            md["grid index y"] = pypx

        # 2. Populate with secondary metadata
        recipe_2 = jpk_meta.get_secondary_meta_recipe()
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
