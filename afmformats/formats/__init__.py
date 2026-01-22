import pathlib

from .. import errors
from .. import meta
from .fmt_hdf5 import recipe_hdf5
from .fmt_igor import recipe_ibw
from .fmt_jpk import (
    recipe_jpk_force,
    recipe_jpk_force_map,
    recipe_jpk_force_qi_data,
    recipe_jpk_force_qi_series,
)
from .fmt_tab import recipe_tab
from .fmt_chiaro_txt import recipe_chiaro_txt
from .fmt_ntmdt_txt import recipe_ntmdt_txt
from .fmt_workshop import recipe_workshop_single, recipe_workshop_map
from ..mod_force_distance import AFMForceDistance
from ..mod_creep_compliance import AFMCreepCompliance
from ..mod_stress_relaxation import AFMStressRelaxation


__all__ = ["AFMFormatRecipe", "find_data", "get_recipe", "load_data",
           "default_data_classes_by_modality", "formats_available",
           "formats_by_suffix", "formats_by_modality", "supported_extensions"]


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

        # check modality
        if not set(self.modalities) <= set(meta.IMAGING_MODALITIES):
            raise ValueError("'modalities' must be in {}, got '{}'!".format(
                meta.IMAGING_MODALITIES, self.modalities))

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
    def modalities(self):
        """list of supported AFM imaging modalities"""
        if "modalities" in self.recipe:
            return self.recipe["modalities"]
        else:
            raise ValueError(f"No modalities defined for recipe {self}!")

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

    def get_modality(self, path):
        """Determine modality of a path

        If a recipe provides several modalities, load the
        dataset and get the modality from the metadata.
        """
        if len(self.modalities) == 1:
            modality = self.modalities[0]
        else:
            fdetect = self.recipe["detect"]
            _, modality = fdetect(path, return_modality=True)
        return modality


def find_data(path, modality=None):
    """Recursively find valid AFM data files

    Parameters
    ----------
    path: str or pathlib.Path
        file or directory
    modality: str
        modality of the measurement ("force-distance")

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
                file_list += find_data(pp, modality=modality)
    else:
        try:
            get_recipe(path=path, modality=modality)
        except errors.FileFormatNotSupportedError:
            # not a valid file format
            pass
        else:
            # valid file format
            file_list.append(path)
    return file_list


def get_recipe(path, modality=None):
    """Return the file format recipe for a given path

    Parameters
    ----------
    path: str or pathlib.Path
        file or directory
    modality: str
        modality of the measurement (see :const:`IMAGING_MODALITIES`)

    Returns
    -------
    recipe: AFMFormatRecipe
        file format recipe
    """
    path = pathlib.Path(path)

    if path.suffix not in formats_by_suffix:
        raise errors.FileFormatNotSupportedError(
            f"No recipe for suffix '{path.suffix}' (file '{path}')!")

    recipes = formats_by_suffix[path.suffix]
    for rec in recipes:
        if ((modality is None or modality in rec.modalities)
                and rec.detect(path)):
            break
    else:
        raise errors.FileFormatNotSupportedError(
            f"Could not determine file format recipe for '{path}'!")

    return rec


def load_data(path, meta_override=None, modality=None,
              data_classes_by_modality=None, diskcache=False,
              callback=None):
    """Load AFM data

    Parameters
    ----------
    path: str or pathlib.Path
        Path to AFM data file
    meta_override: dict
        Metadata dictionary that overrides experimental metadata
    modality: str
        Which acquisition modality to use (e.g. "force-distance")
    data_classes_by_modality: dict
        Override the default AFMData class to use for managing the data
        (see :data:`default_data_classes_by_modality`): This is e.g.
        used by :ref:`nanite:index` to pass `Indentation` (which is a
        subclass of the default `AFMForceDistance`) for handling
        "force-indentation" data.
    diskcache: bool
        Whether to use caching (not implemented)
    callback: callable
        A method that accepts a float between 0 and 1
        to externally track the process of loading the data

    Returns
    -------
    afm_list: list of afmformats.afm_data.AFMData
        List where each element is on AFMData curve
    """
    if meta_override is None:
        meta_override = {}
    if data_classes_by_modality is None:
        data_classes_by_modality = {}
    path = pathlib.Path(path)
    if path.suffix in formats_by_suffix:
        afmdata = []
        cur_recipe = get_recipe(path, modality=modality)
        loader = cur_recipe.loader
        if modality is None:
            modality = cur_recipe.get_modality(path)
            fix_modality = False
        else:
            fix_modality = True
        if modality in data_classes_by_modality:
            afm_data_class = data_classes_by_modality[modality]
        else:
            afm_data_class = default_data_classes_by_modality[modality]
        for dd in loader(path,
                         callback=callback,
                         meta_override=meta_override):
            dd["metadata"]["format"] = "{} ({})".format(cur_recipe["maker"],
                                                        cur_recipe["descr"])
            if fix_modality and dd["metadata"]["imaging mode"] != modality:
                # The user explicitly requested this modality.
                continue
            ddi = afm_data_class(data=dd["data"],
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
    # modality
    for modality in afr.modalities:
        if modality not in formats_by_modality:
            formats_by_modality[modality] = []
        formats_by_modality[modality].append(afr)
    # supported extensions
    if afr.suffix not in supported_extensions:  # avoid duplicates
        supported_extensions.append(afr.suffix)
    supported_extensions.sort()


#: dictionary with default data classes for each modality
default_data_classes_by_modality = {
    "force-distance": AFMForceDistance,
    "creep-compliance": AFMCreepCompliance,
    "stress-relaxation": AFMStressRelaxation,
}

#: available/supported file formats
formats_available = []

#: available file formats in a dictionary with suffix keys
formats_by_suffix = {}

#: available file formats in a dictionary for each modality
formats_by_modality = {}

#: list of supported extensions
supported_extensions = []

for _recipe in [
    recipe_hdf5,
    recipe_ibw,
    recipe_jpk_force,
    recipe_jpk_force_map,
    recipe_jpk_force_qi_data,
    recipe_jpk_force_qi_series,
    recipe_ntmdt_txt,
    recipe_chiaro_txt,
    recipe_tab,
    recipe_workshop_map,
    recipe_workshop_single,
]:
    register_format(_recipe)
