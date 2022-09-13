try:
    from . import common
except Exception as e:
    print("{}: Failed to import `studio.tools.common`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import modeling
except Exception as e:
    print("{}: Failed to import `studio.tools.modeling`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import shading
except Exception as e:
    print("{}: Failed to import `studio.tools.shading`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import rigging
except Exception as e:
    print("{}: Failed to import `studio.tools.rigging`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import layout
except Exception as e:
    print("{}: Failed to import `studio.tools.layout`: {}'".format(e.__class__.__name__, e.message))
