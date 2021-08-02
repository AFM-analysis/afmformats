import pytest

from afmformats import parse_funcs


def assert_false(value):
    assert isinstance(value, bool)
    assert not value


def assert_true(value):
    assert isinstance(value, bool)
    assert value


def test_fbool():
    assert_true(parse_funcs.fbool("true"))
    assert_true(parse_funcs.fbool("True"))
    assert_true(parse_funcs.fbool(True))
    assert_true(parse_funcs.fbool(1))
    assert_true(parse_funcs.fbool(1.0))

    assert_false(parse_funcs.fbool("false"))
    assert_false(parse_funcs.fbool("False"))
    assert_false(parse_funcs.fbool(False))
    assert_false(parse_funcs.fbool(0))
    assert_false(parse_funcs.fbool(0.0))

    with pytest.raises(ValueError):
        parse_funcs.fbool("peter")


def test_fint():
    assert parse_funcs.fint("10") == 10
    assert parse_funcs.fint("-11") == -11
    assert parse_funcs.fint("True") == 1
    assert parse_funcs.fint("true") == 1
    assert parse_funcs.fint("false") == 0
    assert parse_funcs.fint("False") == 0

    with pytest.raises(ValueError):
        parse_funcs.fint("peter")
