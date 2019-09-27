import abc


class AFMData(abc.ABC):
    """General base class for AFM data"""

    @property
    @abc.abstractmethod
    def path(self):
        """Path to the measurement file"""
        # set this to None if it does not apply

    @property
    @abc.abstractmethod
    def index(self):
        """Unique index identifying this dataset in `self.path`

        Indexing starts at '0'.
        """

    @property
    @abc.abstractmethod
    def metadata(self):
        """Metadata, instance of :class:`afmformats.MetaData`)"""
