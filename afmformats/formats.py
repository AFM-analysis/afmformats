import pathlib

from . import errors
from .fmt_hdf5 import recipe_hdf5
from .fmt_igor import recipe_ibw
from .fmt_jpk import recipe_jpk_force, recipe_jpk_force_map, \
    recipe_jpk_force_qi
from .fmt_tab import recipe_tab
from .fmt_ntmdt_txt import recipe_ntmdt_txt
from .fmt_workshop import recipe_workshop_single, recipe_workshop_map
from .afm_fdist import AFMForceDistance


__all__ = ["AFMFormatRecipe", "find_data", "get_recipe", "load_data",
           "formats_available", "formats_by_suffix", "formats_by_mode",
           "supported_extensions"]


#: supported imaging modalities
IMAGING_MODALITIES = ["force-distance"]


class AFMFormatRecipe(object):
    def __init__(self, recipe):
        """A wrapper class for file format recipes

        Parameters
        ----------
        recipe: dict
            file format recipe
        """
        self.recipe = recipe

        # check loader
        if not callable(self.loader):
            raise ValueError(
                "'loader' must be callable: '{}'".format(self.loader))
        self.origin = self.loader.__module__

        # check mode
        if self.mode not in IMAGING_MODALITIES:
            raise ValueError("'mode' must be in {}, got '{}'!".format(
                IMAGING_MODALITIES, self.mode))

        # check detect
        if "detect" in self.recipe:
            if not callable(self.recipe["detect"]):
                raise ValueError(
                    "'detect' must be callable: '{}'".format(
                        self.recipe["detect"]))

    def __getitem__(self, key):
        # backwards compatibility
        return getattr(self, key)

    def __repr__(self):
        repre = "<{} from '{}' at {}>".format(self.__class__.__name__,
                                              self.origin,
                                              hex(id(self)))
        return repre

    @property
    def descr(self):
        """description of file format"""
        return self.recipe.get("descr", "no description")

    @property
    def loader(self):
        """method for loading the data"""
        if "loader" in self.recipe:
            return self.recipe["loader"]
        else:
            raise ValueError("No loader defined!")

    @property
    def maker(self):
        """who introduced the file format"""
        return self.recipe.get("maker", "unknown maker")

    @property
    def mode(self):
        """key describing the AFM recording modality"""
        if "mode" in self.recipe:
            return self.recipe["mode"]
        else:
            raise ValueError("No mode defined for recipe {}!".format(self))

    @property
    def suffix(self):
        """file format suffix"""
        if "suffix" in self.recipe:
            return self.recipe["suffix"]
        else:
            raise ValueError("No suffix defined for recipe {}!".format(self))

    def detect(self, path):
        """Determine whether `path` can be opened with this recipe

        Returns
        -------
        valid: bool
            True if `path` is openable, False otherwise.

        Notes
        -----
        If the underlying recipe does not implement a "detect"
        function, then only the file extension is checked.
        """
        valid = False
        path = pathlib.Path(path)
        # basic check for suffix
        try:
            if path.suffix == self.suffix:
                valid = True
        except ValueError:
            pass

        # advanced check with "detect"
        if valid and "detect" in self.recipe:
            fdetect = self.recipe["detect"]
            valid = fdetect(path)

        return valid


def find_data(path, mode=None):
    """Recursively find valid AFM data files

    Parameters
    ----------
    path: str or pathlib.Path
        file or directory
    mode: str
        mode of the measurement ("force-distance")

    Returns
    -------
    file_list: list of pathlib.Path
        list of valid AFM data files
    """
    path = pathlib.Path(path)
    file_list = []
    if path.is_dir():
        # recurse into subdirectories
        for pp in path.rglob("*"):
            if pp.is_file():
                file_list += find_data(pp, mode=mode)
    else:
        try:
            get_recipe(path=path, mode=mode)
        except errors.FileFormatNotSupportedError:
            # not a valid file format
            pass
        else:
            # valid file format
            file_list.append(path)
    return file_list


def get_recipe(path, mode=None):
    """Return the file format recipe for a given path

    Parameters
    ----------
    path: str or pathlib.Path
        file or directory
    mode: str
        mode of the measurement ("force-distance")

    Returns
    -------
    recipe: dict
        file format recipe
    """
    path = pathlib.Path(path)
    if mode is None:
        # TODO:
        # - Try to figure out the mode somehow
        mode = "force-distance"

    if path.suffix not in formats_by_suffix:
        raise errors.FileFormatNotSupportedError(
            f"No recipe for suffix '{path.suffix}' (file '{path}')!")

    recipes = formats_by_suffix[path.suffix]
    for rec in recipes:
        if rec.mode == mode and rec.detect(path):
            break
    else:
        raise errors.FileFormatNotSupportedError(
            f"Could not determine file format recipe for '{path}'!")

    return rec


def load_data(path, mode=None, diskcache=False, callback=None,
              meta_override=None):
    """Load AFM data

    Parameters
    ----------
    path: str or pathlib.Path
        Path to AFM data file
    mode: str
        Which acquisition mode to use (currently only "force-distance")
    diskcache: bool
        Whether to use caching (not implemented)
    callback: callable
        A method that accepts a float between 0 and 1
        to externally track the process of loading the data
    meta_override: dict
        Metadata dictionary that overrides experimental metadata
    """
    if meta_override is None:
        meta_override = {}
    path = pathlib.Path(path)
    if path.suffix in formats_by_suffix:
        afmdata = []
        cur_recipe = get_recipe(path, mode)
        loader = cur_recipe.loader
        for dd in loader(path, callback=callback,
                         meta_override=meta_override):
            dd["metadata"]["format"] = "{} ({})".format(cur_recipe["maker"],
                                                        cur_recipe["descr"])
            ddi = AFMForceDistance(data=dd["data"],
                                   metadata=dd["metadata"],
                                   diskcache=diskcache)
            afmdata.append(ddi)
    else:
        raise ValueError("Unsupported file extension: '{}'!".format(path))
    return afmdata


def register_format(recipe):
    """Registers a file format from a recipe dictionary"""
    afr = AFMFormatRecipe(recipe)
    formats_available.append(afr)
    # suffix
    if afr.suffix not in formats_by_suffix:
        formats_by_suffix[afr.suffix] = []
    formats_by_suffix[afr.suffix].append(afr)
    # mode
    if afr.mode not in formats_by_mode:
        formats_by_mode[afr.mode] = []
    formats_by_mode[afr.mode].append(afr)
    # supported extensions
    if afr.suffix not in supported_extensions:  # avoid duplucates
        supported_extensions.append(afr.suffix)
    supported_extensions.sort()


#: available/supported file formats
formats_available = []

#: available file formats in a dictionary with suffix keys
formats_by_suffix = {}

#: available file formats in a dictionary with modality keys
formats_by_mode = {}

#: list of supported extensions
supported_extensions = []

for _recipe in [
    recipe_hdf5,
    recipe_ibw,
    recipe_jpk_force,
    recipe_jpk_force_map,
    recipe_jpk_force_qi,
    recipe_ntmdt_txt,
    recipe_tab,
    recipe_workshop_map,
    recipe_workshop_single,
]:
    register_format(_recipe)
