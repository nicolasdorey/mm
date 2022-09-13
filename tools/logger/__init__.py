try:
    from . import extra_logger
except Exception as e:
    print("{}: Failed to import `extra_logger`: {}'".format(e.__class__.__name__, e.message))
