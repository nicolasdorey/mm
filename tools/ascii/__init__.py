try:
    from . import update_string_from_ascii
except Exception as e:
    print("{}: Failed to import `update_string_from_ascii`: {}'".format(e.__class__.__name__, e.message))
