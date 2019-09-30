class AFMFileFormatError(BaseException):
    pass


class FileFormatNotSupportedError(AFMFileFormatError):
    pass


class FileFormatMetaDataError(AFMFileFormatError):
    pass


class DataFileBrokenError(AFMFileFormatError):
    pass
