try:
    from . import rename_modules
except Exception as e:
    print("{}: Failed to import `rename_modules`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import rename_proxy_meshes
except Exception as e:
    print("{}: Failed to import `rename_proxy_meshes`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import spaceswitch
except Exception as e:
    print("{}: Failed to import `spaceswitch`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import spaceswitch_ui
except Exception as e:
    print("{}: Failed to import `spaceswitch_ui`: {}'".format(e.__class__.__name__, e.message))