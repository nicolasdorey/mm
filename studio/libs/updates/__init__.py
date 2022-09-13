try:
    from . import nodes
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.updates.nodes`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import shaders
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.updates.shaders`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import references
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.updates.references`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import layers
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.updates.layers`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import scene
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.updates.scene`: {}'".format(e.__class__.__name__, e.message))
