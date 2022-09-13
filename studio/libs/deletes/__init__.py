try:
    from . import nodes
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.deletes.nodes`: {}'".format(e.__class__.__name__,  e.message))

try:
    from . import shaders
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.deletes.delete_shaders`: {}'".format(e.__class__.__name__,  e.message))

try:
    from . import scene
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.deletes.scene`: {}'".format(e.__class__.__name__,  e.message))