try:
    from . import mod_uvtool
except Exception as e:
    print("{}: Failed to import `mod_uvtool`: {}'".format(e.__class__.__name__, e.message))
