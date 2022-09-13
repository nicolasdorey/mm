try:
    from . import libs
except Exception as e:
    print("{}: Failed to import `fw_maya.libs`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import tools
except Exception as e:
    print("{}: Failed to import `fw_maya.tools`: {}'".format(e.__class__.__name__, e.message))
