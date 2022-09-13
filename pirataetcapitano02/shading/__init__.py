try:
    from . import baking_redshift
except Exception as e:
    print("{}: Failed to import `baking_redshift`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import clean_shading
except Exception as e:
    print("{}: Failed to import `clean_shading`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import out_task_asset
except Exception as e:
    print("{}: Failed to import `out_task_asset`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import set_redshift_attr
except Exception as e:
    print("{}: Failed to import `set_redshift_attr`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import set_redshift_renderer
except Exception as e:
    print("{}: Failed to import `set_redshift_renderer`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import sha_module_connections
except Exception as e:
    print("{}: Failed to import `sha_module_connections`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import sha_module_connections_ui
except Exception as e:
    print("{}: Failed to import `sha_module_connections_ui`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import transfert_map
except Exception as e:
    print("{}: Failed to import `transfert_map`: {}'".format(e.__class__.__name__, e.message))