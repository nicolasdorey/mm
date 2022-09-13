try:
    from . import namespace_to_prefix
except Exception as e:
    print("{}: Failed to import `namespace_to_prefix`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import ref_gallery
except Exception as e:
    print("{}: Failed to import `ref_gallery`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import update_asset_step
except Exception as e:
    print("{}: Failed to import `update_asset_step`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import update_assetLibrary_master
except Exception as e:
    print("{}: Failed to import `update_assetLibrary_master`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import update_assetLibrary_master_bkl
except Exception as e:
    print("{}: Failed to import `update_assetLibrary_master_bkl`: {}'".format(e.__class__.__name__, e.message))
