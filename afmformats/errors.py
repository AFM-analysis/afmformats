class AFMFileFormatError(BaseException):
    pass


class DataFileBrokenError(AFMFileFormatError):
    pass


class FileFormatNotSupportedError(AFMFileFormatError):
    pass


class FileFormatMetaDataError(AFMFileFormatError):
    pass


class InvalidFileFormatError(AFMFileFormatError):
    pass


class MissingMetaDataError(BaseException):
    def __init__(self, meta_keys, *args, **kwargs):
        """Special error class for missing metadata

        The missing metadata keys are stored in the
        ``meta_keys`` property.
        """
        #: List of missing metadata keys
        self.meta_keys = meta_keys
        super(MissingMetaDataError, self).__init__(*args, **kwargs)


__all__ = [e for e in dir() if not e.startswith("__")]
