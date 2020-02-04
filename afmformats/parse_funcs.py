def fbool(value):
    """boolean"""
    if isinstance(value, str):
        value = value.lower()
        if value == "false":
            value = False
        elif value == "true":
            value = True
        elif value:
            value = bool(float(value))
        else:
            raise ValueError("empty string")
    else:
        value = bool(float(value))
    return value


def fint(value):
    """integer"""
    if isinstance(value, str):
        # strings might have been saved wrongly as booleans
        value = value.lower()
        if value == "false":
            value = 0
        elif value == "true":
            value = 1
        elif value:
            value = int(float(value))
        else:
            raise ValueError("empty string")
    else:
        value = int(float(value))
    return value


def vd_str_in(alist):
    """Return a validator that tests whether a string is in a list"""
    def str_in(value):
        if value not in alist:
            raise ValueError("Invalid value '{}', must be in {}!".format(
                value, alist))
        return value
    return str_in


__all__ = [e for e in dir() if not e.startswith("__")]
