import functools
import json
from pkg_resources import resource_filename


__all__ = ["get_primary_meta_recipe",
           "get_secondary_meta_recipe",
           ]


@functools.lru_cache()
def get_primary_meta_recipe():
    with open(resource_filename("afmformats.formats.fmt_jpk",
                                "jpk_meta_primary.json")) as fd:
        meta_recipe_pri = json.load(fd)
    return meta_recipe_pri


@functools.lru_cache()
def get_secondary_meta_recipe():
    with open(resource_filename("afmformats.formats.fmt_jpk",
                                "jpk_meta_secondary.json")) as fd:
        meta_recipe_sec = json.load(fd)
    return meta_recipe_sec
