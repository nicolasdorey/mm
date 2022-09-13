try:
    from . import nodes
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.checks.nodes`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import shaders
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.checks.shaders`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import references
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.checks.references`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import layers
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.checks.layers`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import scene
except Exception as e:
    print("{}: Failed to import `fw_maya.libs.checks.scene`: {}'".format(e.__class__.__name__, e.message))