import pathlib

from .afm_data import AFMData
from .formats import load_data


__all__ = ["AFMGroup"]


class AFMGroup(object):
    """Container for :class:`afmformats.afm_data.AFMData`"""
    def __init__(self, path=None, meta_override=None, callback=None,
                 modality=None, data_classes_by_modality=None):
        """
        Parameters
        ----------
        path: str or pathlib.Path or None
            If this option is specified, then an AFMGroup is generated
            directly from a datafile.
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
        if path is not None:
            path = pathlib.Path(path)
        self._mmlist = []

        if path is not None:
            self += load_data(
                path,
                callback=callback,
                meta_override=meta_override,
                modality=modality,
                data_classes_by_modality=data_classes_by_modality
            )
        elif meta_override is not None:
            raise ValueError("Specifying `meta_override` without specifying "
                             "`path` is meaningless.")

        self.path = path

    def __add__(self, grp):
        out = AFMGroup()
        out += self
        out += grp
        return out

    def __iadd__(self, grp):
        if not isinstance(grp, (AFMGroup, list)):
            raise ValueError("Please specify list or AFMGroup for iadd!")
        for afmdata in grp:
            self.append(afmdata)
        self.path = None
        return self

    def __iter__(self):
        return iter(self._mmlist)

    def __getitem__(self, idx):
        return self._mmlist[idx]

    def __len__(self):
        return len(self._mmlist)

    def __repr__(self):
        return f"<{self.__class__.__name__}: '{self.path}' at {hex(id(self))}>"

    def __str__(self):
        rep = [f"{self.__class__.__name__}: '{self.path}'"]
        for afmdata in self._mmlist:
            rep.append("- {}".format(afmdata))
        return "\n".join(rep)

    def append(self, afmdata):
        """Append an AFMData instance

        Parameters
        ----------
        afmdata: afmformats.afm_data.AFMData
            AFM data
        """
        if not isinstance(afmdata, AFMData):
            raise ValueError("`afmdata` must be an instance of `AFMData`!")
        self._mmlist.append(afmdata)

    def get_enum(self, enum):
        """Return the AFMData curve with this enum value

        Raises
        ------
        ValueError if multiple curves with the same enum value exist.
        KeyError if the enum value is not found
        """
        curves = []
        for afmdata in self._mmlist:
            if afmdata.enum == enum:
                curves.append(afmdata)
        if len(curves) == 0:
            raise KeyError(f"Could not find dataset with enum '{enum}'!")
        elif len(curves) == 1:
            return curves[0]
        else:
            raise ValueError(
                f"Multiple curves with the enum value '{enum}' exist!")

    def index(self, afmdata):
        return self._mmlist.index(afmdata)

    def subgroup_with_path(self, path):
        """Return a subgroup with AFMData matching `path`"""
        path = pathlib.Path(path)
        subgroup = AFMGroup()
        for afmdata in self:
            if afmdata.path.samefile(path):
                subgroup.append(afmdata)
        subgroup.path = path
        return subgroup
