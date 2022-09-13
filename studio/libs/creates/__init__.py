try:
    from . import shaders
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.creates.shaders`: {}'".format(e.__class__.__name__, e.message))
