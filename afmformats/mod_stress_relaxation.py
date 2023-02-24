from .afm_data import AFMData
from .afm_segment import AFMSegment


__all__ = ["AFMStressRelaxation"]


class AFMStressRelaxation(AFMData):
    """Base class for AFM stress-relaxation data

    A stress-relaxation dataset consists of a pre-approach (with
    constant height), an approach (with a predefined indentation depth),
    an intermediate (with constant height), and a retract curve.
    """
    def __init__(self, *args, **kwargs):
        super(AFMStressRelaxation, self).__init__(*args, **kwargs)
        #: Dictionary-like interface to the pre-measurement segment
        self.prep = AFMSegment(self._raw_data, self._data, segment=0)
        #: Dictionary-like interface to the approach segment
        self.appr = AFMSegment(self._raw_data, self._data, segment=1)
        #: Dictionary-like interface to the intermediate segment
        self.intr = AFMSegment(self._raw_data, self._data, segment=2)
        #: Dictionary-like interface to the retract segment
        self.retr = AFMSegment(self._raw_data, self._data, segment=3)

    def __setitem__(self, key, value):
        super(AFMStressRelaxation, self).__setitem__(key, value)
        if key == "segment":
            # The user changed the segment, which means we have to clear
            # the segment cache.
            self.prep.clear_cache()
            self.appr.clear_cache()
            self.intr.clear_cache()
            self.retr.clear_cache()

    @property
    def modality(self):
        """Imaging modality"""
        return "stress-relaxation"
