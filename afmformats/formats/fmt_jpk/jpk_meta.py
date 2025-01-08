import functools
import json
import importlib.resources as importlib_resources

__all__ = ["get_primary_meta_recipe",
           "get_secondary_meta_recipe",
           ]


@functools.lru_cache()
def get_primary_meta_recipe():
    ref = importlib_resources.files(
        "afmformats.formats.fmt_jpk") / "jpk_meta_primary.json"
    with importlib_resources.as_file(ref) as path:
        with open(path) as fd:
            meta_recipe_pri = json.load(fd)
    return meta_recipe_pri


@functools.lru_cache()
def get_secondary_meta_recipe():
    ref = importlib_resources.files(
        "afmformats.formats.fmt_jpk") / "jpk_meta_secondary.json"
    with importlib_resources.as_file(ref) as path:
        with open(path) as fd:
            meta_recipe_sec = json.load(fd)
    return meta_recipe_sec
