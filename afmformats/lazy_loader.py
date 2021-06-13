__all__ = ["LazyData"]


class LazyData(object):
    """Lazily load data from function and kwargs

    The idea is that the experimental data does not have
    to be loaded before the user requests it. Furthermore,
    this reduces the memory footprint (not all data are
    loaded).
    """
    def __init__(self):
        self.loaders = {}

    def __deepcopy__(self, memo):
        # Make sure deepcopy does not copy anything.
        # We might have `io`s, etc.
        return self

    def __contains__(self, key):
        return key in self.loaders

    def __getitem__(self, key):
        if key in self:
            func, kwargs = self.loaders[key]
            return func(**kwargs)

    def __iter__(self):
        for column in self.loaders:
            yield column

    def keys(self):
        return self.loaders.keys()

    def set_lazy_loader(self, column, func, kwargs):
        """Add a lazy loader

        Parameters
        ----------
        column: str
            Column for which to register the loader
        func: callable
            Function to call to get the data
        kwargs:
            Keyword arguments to ``func``
        """
        self.loaders[column] = (func, kwargs)
