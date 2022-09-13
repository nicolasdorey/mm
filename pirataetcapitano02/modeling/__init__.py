try:
    from . import detect_sym_auto
except Exception as e:
    print("{}: Failed to import `detect_sym_auto`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import mdl_checker
except Exception as e:
    print("{}: Failed to import `mdl_checker`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import mdl_checker_master
except Exception as e:
    print("{}: Failed to import `mdl_checker_master`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import out_task_assembly
except Exception as e:
    print("{}: Failed to import `out_task_assembly`: {}'".format(e.__class__.__name__, e.message))

try:
    from . import test_read_button_json
except Exception as e:
    print("{}: Failed to import `test_read_button_json`: {}'".format(e.__class__.__name__, e.message))