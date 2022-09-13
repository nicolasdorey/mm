try:
    from . import rig_autorootwalk
except Exception as e:
    print("{}: Failed to import `rig_autorootwalk`: {}'".format(e.__class__.__name__, e.message))
