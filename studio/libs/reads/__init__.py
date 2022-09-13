try:
    from . import nodes
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.reads.nodes`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import shaders
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.reads.shaders`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import references
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.reads.references`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import layers
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.reads.layers`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import scene
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.reads.scene`: {}'".format(e.__class__.__name__, e.message))
