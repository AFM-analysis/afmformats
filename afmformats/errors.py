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
    pass


__all__ = [e for e in dir() if not e.startswith("__")]
