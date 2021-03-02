"""Test AFMFormatRecipe"""
import afmformats


def test_bad_recipe_loader_missing():
    recipe = {
        "descr": "unknown description",
        "maker": "unknown maker",
        "mode": "force-distance",
        "suffix": ".unknown",
    }
    try:
        afmformats.formats.register_format(recipe)
    except ValueError:
        pass
    else:
        assert False


def test_bad_recipe_loader_not_callable():
    recipe = {
        "descr": "unknown description",
        "loader": "peter",
        "maker": "unknown maker",
        "mode": "force-distance",
        "suffix": ".unknown",
    }
    try:
        afmformats.formats.register_format(recipe)
    except ValueError:
        pass
    else:
        assert False


def test_bad_recipe_mode_invlaid():
    recipe = {
        "descr": "unknown description",
        "loader": lambda x: x,
        "maker": "unknown maker",
        "suffix": ".unknown",
        "mode": "invalid",
    }
    try:
        afmformats.formats.register_format(recipe)
    except ValueError:
        pass
    else:
        assert False


def test_bad_recipe_mode_missing():
    recipe = {
        "descr": "unknown description",
        "loader": lambda x: x,
        "maker": "unknown maker",
        "suffix": ".unknown",
    }
    try:
        afmformats.formats.register_format(recipe)
    except ValueError:
        pass
    else:
        assert False


def test_bad_recipe_suffix_missing():
    recipe = {
        "descr": "unknown description",
        "loader": lambda x: x,
        "maker": "unknown maker",
        "mode": "force-distance",
    }
    try:
        afmformats.formats.register_format(recipe)
    except ValueError:
        pass
    else:
        assert False


if __name__ == "__main__":
    # Run all tests
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
