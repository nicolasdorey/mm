try:
    from . import dicts
except Exception as e:
    print("{}: Failed to import `fw_common.libs.dicts`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import json
except Exception as e:
    print("{}: Failed to import `fw_common.libs.json`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import system
except Exception as e:
    print("{}: Failed to import `fw_common.libs.system`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import sgtk
except Exception as e:
    print("{}: Failed to import `fw_common.libs.sgtk`: {}'".format(e.__class__.__name__, e.message))
