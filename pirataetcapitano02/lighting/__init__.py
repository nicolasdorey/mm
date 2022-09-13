try:
    from . import lighting_manager
except Exception as e:
    print("{}: Failed to import `lighting_manager`: {}'".format(e.__class__.__name__, e.message))
