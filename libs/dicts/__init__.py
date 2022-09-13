try:
    from . import reads
except Exception as e:
    print("{}: Failed to import `fw_common.dicts.reads`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import updates
except Exception as e:
    print("{}: Failed to import `fw_common.dicts.updates`: {}'".format(e.__class__.__name__, e.message))
