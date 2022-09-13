try:
    from . import widgets
except Exception as e:
    print("{}: Failed to import `fw_common.tools.sgtk.widgets`: {}'".format(e.__class__.__name__, e.message))
