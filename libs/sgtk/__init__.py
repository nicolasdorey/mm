try:
    from . import reads
except Exception as e:
    print("{}: Failed to import `fw_common.sgtk.reads`: {}'".format(e.__class__.__name__, e.message))
